# UART Slave Tester — Raspberry Pi

Tests all three UART slave devices (**SERVO**, **STEPPER**, **RADAR**) by sending commands to the Pico Master over UART and verifying responses.

## Architecture

```
Raspberry Pi
  └─ /dev/ttyAMA0 @ 460800 baud
       └─ Pico Master (UART0)
            └─ Shared UART1 bus @ 115200 baud
                 ├─ SERVO slave
                 ├─ STEPPER slave
                 └─ RADAR slave
```

## Requirements

```bash
pip install pyserial
```

UART must be enabled on the Raspberry Pi:

```bash
sudo raspi-config
# Interface Options -> Serial Port
# "Would you like a login shell over serial?" -> No
# "Would you like the serial port hardware to be enabled?" -> Yes
```

## Usage

```bash
# Test all devices
python3 test_uart_slaves.py

# Test a single device
python3 test_uart_slaves.py --device SERVO
python3 test_uart_slaves.py --device STEPPER
python3 test_uart_slaves.py --device RADAR
python3 test_uart_slaves.py --device MASTER

# Custom serial port
python3 test_uart_slaves.py --port /dev/ttyUSB0

# Show raw send/receive lines
python3 test_uart_slaves.py --verbose

# Combine options
python3 test_uart_slaves.py --device RADAR --verbose

# If permission denied
sudo python3 test_uart_slaves.py
```

## Test Coverage

| Device  | Commands Tested |
|---------|----------------|
| MASTER  | `PING`, `STATUS` |
| SERVO   | `PING`, `WHOAMI`, `STATUS`, `OPEN`, `STATUS`, `CLOSE`, `STATUS` |
| STEPPER | `PING`, `WHOAMI`, `STATUS`, `SPIN:50`, `STATUS`, `STOP`, `STATUS` |
| RADAR   | `PING`, `WHOAMI`, `STATUS`, `READ` × 3 |

## Response Timeouts

These account for the Pico's own slave timeouts plus round-trip overhead:

| Device  | Timeout |
|---------|---------|
| MASTER  | 3 s     |
| SERVO   | 12 s    |
| STEPPER | 6 s     |
| RADAR   | 4 s     |

## Example Output

```
=======================================================
  Raspberry Pi → Pico Master → UART Slaves Tester
=======================================================
  Port   : /dev/ttyAMA0
  Baud   : 460800
  Devices: ALL

✓ Connected to /dev/ttyAMA0 @ 460800 baud

═══════════════════════════════════════════════════════
 MASTER
═══════════════════════════════════════════════════════
  [PASS] MASTER:PING
  [PASS] MASTER:STATUS
       Slaves configured: ['SERVO', 'STEPPER', 'RADAR']

═══════════════════════════════════════════════════════
 SERVO
═══════════════════════════════════════════════════════
  [PASS] SERVO:PING
  [PASS] SERVO:WHOAMI
  [PASS] SERVO:STATUS
  Opening actuator (up to 12 s) …
  [PASS] SERVO:OPEN
  [PASS] SERVO:STATUS (after OPEN)
  Closing actuator (up to 12 s) …
  [PASS] SERVO:CLOSE
  [PASS] SERVO:STATUS (after CLOSE)

...

═══════════════════════════════════════════════════════
 RESULTS SUMMARY
═══════════════════════════════════════════════════════
  MASTER     2/2 passed  [OK]
  SERVO      7/7 passed  [OK]
  STEPPER    7/7 passed  [OK]
  RADAR      6/6 passed  [OK]
  ─────────────────────────────────────────────────────
  Total: 22 passed, 0 failed  →  ALL PASSED
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Cannot open /dev/ttyAMA0` | UART not enabled or port wrong | Run `raspi-config`, enable serial hardware; check `ls /dev/ttyAMA*` |
| Permission denied | User not in `dialout` group | `sudo usermod -aG dialout $USER` then re-login, or run with `sudo` |
| All devices timeout | Pico Master not running or wrong baud | Flash `main.py` to Pico; verify baud matches (460800) |
| Single device timeout | Slave not connected or not powered | Check wiring on UART1 bus; verify slave firmware is running |
| Non-JSON response | Pico still booting | Wait a few seconds and retry |
