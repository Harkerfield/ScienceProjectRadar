#!/usr/bin/env python3
"""
Raspberry Pi UART Slave Tester
Tests all three UART slave devices (servo, stepper, RADAR) through the Pico Master.

Architecture:
    Raspberry Pi -> [UART0 @ 460800] -> Pico Master -> [UART1 @ 115200] -> Slaves

Run with:
    python3 test_uart_slaves.py
    python3 test_uart_slaves.py --device servo
    python3 test_uart_slaves.py --port /dev/ttyUSB0
    python3 test_uart_slaves.py --verbose
"""

import serial
import json
import time
import sys
import argparse
from datetime import datetime

# ── Configuration ─────────────────────────────────────────────────────────────

PORT    = "/dev/ttyAMA0"
BAUD    = 460800
TIMEOUT = 10.0          # Serial read timeout (seconds)

# Per-device response timeouts (must exceed Pico slave timeouts)
DEVICE_TIMEOUTS = {
    "master":  3.0,
    "servo":  12.0,   # open/close take ~6 s each on the slave
    "stepper": 6.0,
    "RADAR":   4.0,
}

# ── Helpers ────────────────────────────────────────────────────────────────────

class Colors:
    OK    = "\033[92m"   # green
    FAIL  = "\033[91m"   # red
    WARN  = "\033[93m"   # yellow
    INFO  = "\033[94m"   # blue
    BOLD  = "\033[1m"
    RESET = "\033[0m"

def _c(color: str, text: str) -> str:
    return f"{color}{text}{Colors.RESET}"

def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


class UARTSlaveTester:
    def __init__(self, port: str, baud: int, verbose: bool = False):
        self.port    = port
        self.baud    = baud
        self.verbose = verbose
        self.ser     = None
        self.results: dict[str, list[dict]] = {}

    # ── Connection ──────────────────────────────────────────────────────────

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=TIMEOUT)
            time.sleep(0.5)          # Let the Pico settle
            print(_c(Colors.OK, f"✓ Connected to {self.port} @ {self.baud} baud"))
            return True
        except serial.SerialException as exc:
            print(_c(Colors.FAIL, f"✗ Cannot open {self.port}: {exc}"))
            print("  Troubleshooting:")
            print("    - Is UART enabled?  sudo raspi-config -> Interface Options -> Serial Port")
            print("    - Check:            cat /boot/firmware/config.txt | grep uart")
            print("    - Try:              sudo python3 test_uart_slaves.py")
            return False

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

    # ── Low-level send / receive ────────────────────────────────────────────

    def _flush(self):
        """Discard any bytes already in the receive buffer."""
        time.sleep(0.05)
        self.ser.reset_input_buffer()

    def send_command(self, command: str, timeout: float | None = None) -> dict | None:
        """
        Send *command* to the Pico Master and return the parsed JSON response.

        Returns a dict on success, or None on timeout / parse error.
        """
        device  = command.split(":")[0].upper()
        timeout = timeout or DEVICE_TIMEOUTS.get(device, 5.0)

        if self.verbose:
            print(f"  [{_ts()}] → {command}")

        try:
            self._flush()
            self.ser.write(f"{command}\n".encode())

            deadline = time.time() + timeout
            raw      = b""

            while time.time() < deadline:
                chunk = self.ser.read(self.ser.in_waiting or 1)
                if chunk:
                    raw += chunk
                    if b"\n" in raw:
                        line = raw.split(b"\n")[0].strip()
                        if line:
                            break
                time.sleep(0.01)
            else:
                if self.verbose:
                    print(_c(Colors.WARN, f"  [{_ts()}] ← (timeout after {timeout}s)"))
                return None

            text = line.decode("utf-8", errors="replace")
            if self.verbose:
                print(f"  [{_ts()}] ← {text}")

            return json.loads(text)

        except json.JSONDecodeError:
            if self.verbose:
                print(_c(Colors.WARN, f"  [{_ts()}] ← (non-JSON: {text!r})"))
            return {"s": "ok", "raw": text}     # Return raw text wrapped in a dict
        except Exception as exc:
            print(_c(Colors.FAIL, f"  [{_ts()}] ← error: {exc}"))
            return None

    # ── Test bookkeeping ────────────────────────────────────────────────────

    def _record(self, device: str, test_name: str, passed: bool, detail: str = ""):
        self.results.setdefault(device, []).append(
            {"test": test_name, "passed": passed, "detail": detail}
        )
        icon   = _c(Colors.OK, "PASS") if passed else _c(Colors.FAIL, "FAIL")
        suffix = f"  {_c(Colors.WARN, detail)}" if detail else ""
        print(f"  [{icon}] {test_name}{suffix}")

    def _assert_response(self, device: str, test_name: str,
                         response: dict | None,
                         expect_ok: bool = True,
                         detail: str = "") -> bool:
        if response is None:
            self._record(device, test_name, False, "no response (timeout)")
            return False

        ok = (response.get("s") == "ok")
        passed = ok if expect_ok else not ok
        self._record(device, test_name, passed, detail or str(response))
        return passed

    # ── master tests ────────────────────────────────────────────────────────

    def test_master(self):
        print(f"\n{_c(Colors.BOLD, '═' * 55)}")
        print(_c(Colors.BOLD, " master"))
        print(_c(Colors.BOLD, '═' * 55))

        r = self.send_command("master:ping")
        self._assert_response("master", "master:ping", r)

        r = self.send_command("master:status")
        self._assert_response("master", "master:status", r)
        if r and r.get("s") == "ok":
            slaves = r.get("slaves_configured", [])
            print(f"       Slaves configured: {slaves}")

    # ── servo tests ─────────────────────────────────────────────────────────

    def test_servo(self):
        print(f"\n{_c(Colors.BOLD, '═' * 55)}")
        print(_c(Colors.BOLD, " servo"))
        print(_c(Colors.BOLD, '═' * 55))

        r = self.send_command("servo:ping")
        if not self._assert_response("servo", "servo:ping", r):
            print(_c(Colors.WARN, "  Skipping further servo tests (no ping response)"))
            return

        r = self.send_command("servo:whoami")
        self._assert_response("servo", "servo:whoami", r)

        r = self.send_command("servo:status")
        self._assert_response("servo", "servo:status", r)
        if r and r.get("s") == "ok":
            data = r.get("data", {})
            if data:
                print(f"       Status data: {data}")

        print("  Opening actuator (up to 12 s) …")
        r = self.send_command("servo:open", timeout=12.0)
        self._assert_response("servo", "servo:open", r)

        r = self.send_command("servo:status")
        self._assert_response("servo", "servo:status (after open)", r)

        print("  Closing actuator (up to 12 s) …")
        r = self.send_command("servo:close", timeout=12.0)
        self._assert_response("servo", "servo:close", r)

        r = self.send_command("servo:status")
        self._assert_response("servo", "servo:status (after close)", r)

    # ── stepper tests ───────────────────────────────────────────────────────

    def test_stepper(self):
        print(f"\n{_c(Colors.BOLD, '═' * 55)}")
        print(_c(Colors.BOLD, " stepper"))
        print(_c(Colors.BOLD, '═' * 55))

        r = self.send_command("stepper:ping")
        if not self._assert_response("stepper", "stepper:ping", r):
            print(_c(Colors.WARN, "  Skipping further stepper tests (no ping response)"))
            return

        r = self.send_command("stepper:whoami")
        self._assert_response("stepper", "stepper:whoami", r)

        r = self.send_command("stepper:status")
        self._assert_response("stepper", "stepper:status", r)
        if r and r.get("s") == "ok":
            data = r.get("data", {})
            if data:
                print(f"       Status data: {data}")

        print("  Spinning at speed 50 …")
        r = self.send_command("stepper:spin:50")
        self._assert_response("stepper", "stepper:spin:50", r)

        r = self.send_command("stepper:status")
        self._assert_response("stepper", "stepper:status (spinning)", r)

        time.sleep(1.0)

        print("  Stopping stepper …")
        r = self.send_command("stepper:stop")
        self._assert_response("stepper", "stepper:stop", r)

        r = self.send_command("stepper:status")
        self._assert_response("stepper", "stepper:status (stopped)", r)

    # ── RADAR tests ─────────────────────────────────────────────────────────

    def test_radar(self):
        print(f"\n{_c(Colors.BOLD, '═' * 55)}")
        print(_c(Colors.BOLD, " RADAR"))
        print(_c(Colors.BOLD, '═' * 55))

        r = self.send_command("RADAR:ping")
        if not self._assert_response("RADAR", "RADAR:ping", r):
            print(_c(Colors.WARN, "  Skipping further RADAR tests (no ping response)"))
            return

        r = self.send_command("RADAR:whoami")
        self._assert_response("RADAR", "RADAR:whoami", r)

        r = self.send_command("RADAR:status")
        self._assert_response("RADAR", "RADAR:status", r)

        print("  Reading sensor (3 consecutive reads) …")
        for i in range(1, 4):
            r = self.send_command("RADAR:read")
            passed = self._assert_response("RADAR", f"RADAR:read #{i}", r)
            if passed and r:
                data = r.get("data", {})
                dist = data.get("distance", "?")
                conf = data.get("confidence", "?")
                move = data.get("movement", "?")
                print(f"       distance={dist}cm  confidence={conf}%  movement={move}")
            time.sleep(0.3)

    # ── Summary ─────────────────────────────────────────────────────────────

    def print_summary(self):
        print(f"\n{_c(Colors.BOLD, '═' * 55)}")
        print(_c(Colors.BOLD, " RESULTS SUMMARY"))
        print(_c(Colors.BOLD, '═' * 55))

        total_pass = 0
        total_fail = 0

        for device, tests in self.results.items():
            passed = sum(1 for t in tests if t["passed"])
            failed = len(tests) - passed
            total_pass += passed
            total_fail += failed
            status = _c(Colors.OK, "OK") if failed == 0 else _c(Colors.FAIL, "FAIL")
            print(f"  {device:<10} {passed}/{len(tests)} passed  [{status}]")

        print(_c(Colors.BOLD, "─" * 55))
        overall = _c(Colors.OK, "ALL PASSED") if total_fail == 0 else _c(Colors.FAIL, f"{total_fail} FAILED")
        print(f"  Total: {total_pass} passed, {total_fail} failed  →  {overall}")

    # ── Entry points ────────────────────────────────────────────────────────

    def run(self, devices: list[str]):
        """Run tests for the given device list (or all if empty)."""
        if not self.connect():
            return False

        try:
            run_all = not devices

            if run_all or "master" in devices:
                self.test_master()
            if run_all or "servo" in devices:
                self.test_servo()
            if run_all or "stepper" in devices:
                self.test_stepper()
            if run_all or "RADAR" in devices:
                self.test_radar()
        finally:
            self.disconnect()

        self.print_summary()
        total_fail = sum(
            1 for tests in self.results.values()
            for t in tests if not t["passed"]
        )
        return total_fail == 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Test UART slave devices through the Pico Master"
    )
    parser.add_argument(
        "--port", default=PORT,
        help=f"Serial port (default: {PORT})"
    )
    parser.add_argument(
        "--baud", type=int, default=BAUD,
        help=f"Baud rate (default: {BAUD})"
    )
    parser.add_argument(
        "--device", metavar="DEV",
        choices=["master", "servo", "stepper", "RADAR"],
        action="append", dest="devices", default=[],
        help="Device(s) to test; omit to test all"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show raw send/receive lines"
    )
    args = parser.parse_args()

    print("=" * 55)
    print("  Raspberry Pi → Pico Master → UART Slaves Tester")
    print("=" * 55)
    print(f"  Port   : {args.port}")
    print(f"  Baud   : {args.baud}")
    devices_label = ", ".join(args.devices) if args.devices else "ALL"
    print(f"  Devices: {devices_label}")
    print()

    tester = UARTSlaveTester(args.port, args.baud, verbose=args.verbose)
    success = tester.run([d.upper() for d in args.devices])
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
