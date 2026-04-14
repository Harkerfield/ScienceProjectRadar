# v.Final J. 2026-04-13
# Master controller code for Raspberry Pi Pico using MicroPython
# MicroPython UART Master for Raspberry Pi Pico
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
#
# UART Master - Request-response architecture with device addressing
# REQUEST-RESPONSE ARCHITECTURE: Server -> Master -> Slaves -> Master -> Server
#
# UART Slaves (on shared UART1 bus with device addressing):
#   - servo: open|close|status|whoami|ping
#   - stepper: spin|stop|status|whoami|ping
#   - radar: read|status|whoami|ping
#
# Command Format: device:command[:args]
# Response Format: device:status[:data]
#
# UART Connections:
#   - UART0: Server communication (TX=Pin(16), RX=Pin(17))
#   - UART1: Slave communication bus (TX=Pin(4), RX=Pin(5))


from machine import UART, Pin
import utime
from utime import sleep
import sys
import select

# LED on pin 25 (Pico's built-in LED)
led = Pin("LED", Pin.OUT)
led.on()  # Turn on LED while processing to indicate activity

# UART0: Server communication (request source)
uart_server = UART(0, baudrate=460800, tx=Pin(16), rx=Pin(17))

# UART1: Slave communication (shared bus with device addressing)
uart_slaves = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))

# Slave device definitions
SLAVES = {
    "servo": {"timeout_ms": 8000, "description": "Servo servo"},
    "stepper": {"timeout_ms": 5000, "description": "Stepper Motor"},
    "radar": {"timeout_ms": 3000, "description": "Radar Sensor"},  # Increased for shared bus
}

# Common device names to attempt discovery during startup (allows dynamic discovery)
DISCOVERABLE_DEVICES = ["servo", "stepper", "radar"]  # Devices to try discovering even if not in SLAVES

# Device command registry - populated at startup
device_commands = {"master": ["ping", "status", "commands", "whoami", "rediscover", "scan", "force"]}  # Format: {"servo": ["ping", "open", "close", ...], ...}
devices_initialized = False  # Flag to track if device discovery is complete
initialization_attempts = 0  # Track retry attempts

print("[STARTUP] UART Master initialized")
print(f"[STARTUP] Slave devices configured: {', '.join(SLAVES.keys())}")
print("[STARTUP] Waiting for server commands...\n")

# ============ UART COMMUNICATION LAYER ============

def flush_uart_buffer():
    """Clear any stale data in UART buffer"""
    while uart_slaves.any():
        uart_slaves.read()
    utime.sleep_ms(50)

def send_uart_command_raw(device, cmd, timeout_ms=3000):
    """
    Send raw command to device without checking SLAVES config.
    Used for network scanning and discovery.
    
    Returns:
        Response string or None if timeout/error
    """
    full_cmd = f"{device}:{cmd}\n"
    
    try:
        # Flush buffer before sending to clear any stale data
        flush_uart_buffer()
        utime.sleep_ms(50)
        
        # Send command
        print(f"[SCAN-SEND] {device}:{cmd}")
        uart_slaves.write(full_cmd.encode())
        utime.sleep_ms(20)  # Allow TX to complete
        
        # Wait for slave to process and respond
        utime.sleep_ms(100)
        
        # Read actual slave response until newline or timeout
        response = bytearray()
        start_time = utime.ticks_ms()
        
        while (utime.ticks_ms() - start_time) < timeout_ms:
            if uart_slaves.any():
                byte = uart_slaves.read(1)
                if byte == b'\n':
                    if response:
                        resp_text = bytes(response).decode().strip()
                        print(f"[SCAN-RECV] {resp_text}")
                        return resp_text
                    # Empty line, keep reading
                elif byte:
                    response += byte
            else:
                utime.sleep_ms(5)
        
        return None
        
    except Exception as e:
        print(f"[SCAN-ERR] Communication with {device} failed: {e}")
        return None

def network_scan(device_names=None, timeout_ms=3000):
    """
    Scan the UART network for responding devices.
    Completely independent of SLAVES configuration.
    
    Args:
        device_names: List of device names to scan for (default: common names)
        timeout_ms: Timeout per device query in milliseconds
    
    Returns:
        Dictionary with format: {"found_devices": {...}, "total_scanned": N}
    """
    if device_names is None:
        device_names = ["servo", "stepper", "radar", "sensor", "motor", "controller"]
    
    print("\n" + "=" * 70)
    print("NETWORK SCAN: Searching for UART devices...")
    print("=" * 70)
    print(f"Scanning for devices: {', '.join(device_names)}\n")
    
    found_devices = {}
    
    for device_name in device_names:
        print(f"→ Scanning for '{device_name}'...")
        
        # Try to query commands endpoint
        resp = send_uart_command_raw(device_name, "commands", timeout_ms=timeout_ms)
        
        if resp:
            # Parse response
            try:
                parts = resp.split(":")
                if len(parts) >= 3 and parts[1].lower() == "ok":
                    # Extract commands from response
                    for part in parts[2:]:
                        if part.startswith("commands="):
                            cmd_list = part.split("=", 1)[1].split(",")
                            found_devices[device_name] = {
                                "commands": cmd_list,
                                "response": resp
                            }
                            print(f"  ✓ Found: {device_name} with {len(cmd_list)} commands")
                            break
                    else:
                        print(f"  ✗ Invalid response format from {device_name}")
                else:
                    print(f"  ✗ Error response from {device_name}")
            except Exception as e:
                print(f"  ✗ Parse error: {e}")
        else:
            print(f"  ✗ No response (timeout)")
        
        utime.sleep_ms(200)  # Delay between scans to prevent bus collision
    
    print("\n" + "=" * 70)
    print("NETWORK SCAN COMPLETE")
    print("=" * 70)
    print(f"Found {len(found_devices)} device(s)")
    for device, info in found_devices.items():
        print(f"  • {device}: {', '.join(info['commands'])}")
    print("=" * 70 + "\n")
    
    return {
        "found_devices": found_devices,
        "total_scanned": len(device_names),
        "total_found": len(found_devices)
    }

def send_device_command(device, cmd, timeout_ms=None):
    """
    Send device-addressed command to slave and wait for response.
    Validates that command exists in device registry before sending.
    
    Returns:
        Response string or None if timeout/error
    """
    if device not in SLAVES:
        print(f"[UART-ERR] Unknown device: {device}")
        return None
    
    if timeout_ms is None:
        timeout_ms = SLAVES[device]["timeout_ms"]
    
    # Extract base command (before any colon args)
    base_cmd = cmd.split(':')[0].lower()
    
    # Validate command is supported (except for "commands" which discovers supported commands)
    if base_cmd != "commands" and device in device_commands:
        if base_cmd not in device_commands[device]:
            print(f"[UART-ERR] Command '{base_cmd}' not supported on {device}")
            print(f"           Available commands: {', '.join(device_commands[device])}")
            return None
    
    # Format: device:command
    full_cmd = f"{device}:{cmd}\n"
    
    try:
        # Flush buffer before sending
        flush_uart_buffer()
        utime.sleep_ms(50)
        
        # Send command
        print(f"[UART-SEND] {device}:{cmd}")
        uart_slaves.write(full_cmd.encode())
        utime.sleep_ms(20)  # Allow TX to complete
        
        # Wait for slave to process and respond
        utime.sleep_ms(100)
        
        # Now read actual slave response until newline or timeout
        response = bytearray()
        start_time = utime.ticks_ms()
        
        while (utime.ticks_ms() - start_time) < timeout_ms:
            if uart_slaves.any():
                byte = uart_slaves.read(1)
                if byte == b'\n':
                    if response:
                        resp_text = bytes(response).decode().strip()
                        print(f"[UART-RECV] {resp_text}")
                        return resp_text
                elif byte:
                    response += byte
            else:
                utime.sleep_ms(5)
        
        print(f"[UART-TIMEOUT] No response from {device} after {timeout_ms}ms")
        return None
        
    except Exception as e:
        print(f"[UART-ERR] Communication with {device} failed: {e}")
        return None

def initialize_device_registry():
    """
    Query all configured devices for their available commands using network scan.
    Populates the global device_commands registry.
    
    Returns:
        True if all devices found and registry populated, False otherwise
    """
    global device_commands, devices_initialized
    
    print("\n" + "=" * 70)
    print("DEVICE DISCOVERY: Initializing device registry")
    print("=" * 70)
    
    # Master is always available
    if "master" not in device_commands:
        device_commands["master"] = ["ping", "status", "commands", "whoami", "rediscover", "scan", "force"]
    print(f"  ✓ master: {len(device_commands['master'])} commands (always available)\n")
    
    # Use network scan to discover devices
    scan_result = network_scan(DISCOVERABLE_DEVICES, timeout_ms=5000)
    
    # Populate device_commands from scan results
    for device_name, device_info in scan_result["found_devices"].items():
        device_commands[device_name] = device_info["commands"]
    
    # Check if all devices were found
    if scan_result["total_found"] == len(DISCOVERABLE_DEVICES):
        devices_initialized = True
        print("=" * 70)
        print("DEVICE DISCOVERY COMPLETE: All devices responded")
        print("=" * 70)
        return True
    else:
        print("\n" + "=" * 70)
        print("WARNING: Device discovery incomplete!")
        print(f"Found {scan_result['total_found']}/{len(DISCOVERABLE_DEVICES)} slave devices (master always available)")
        print("Master will continue with partial device list")
        print("=" * 70 + "\n")
        devices_initialized = (scan_result["total_found"] > 0)
        return False

def get_device_commands(device_name):
    """
    Get available commands for a device.
    If not in registry, query device and cache result.
    
    Args:
        device_name: Name of device (e.g., "stepper")
    
    Returns:
        List of command strings or None if device not found
    """
    global device_commands
    
    device_lower = device_name.lower()
    
    # Check if already in registry
    if device_lower in device_commands:
        return device_commands[device_lower]
    
    # Check if it's a known device but not yet queried
    if device_lower in SLAVES:
        print(f"[REGISTRY] Querying {device_lower}:commands (not in cache)...")
        resp = send_device_command(device_lower, "commands", timeout_ms=2000)
        
        if resp:
            try:
                parts = resp.split(":")
                if len(parts) >= 3 and parts[1].lower() == "ok":
                    for part in parts[2:]:
                        if part.startswith("commands="):
                            cmd_list = part.split("=", 1)[1].split(",")
                            device_commands[device_lower] = cmd_list
                            print(f"[REGISTRY] {device_lower} cached: {', '.join(cmd_list)}")
                            return cmd_list
            except Exception as e:
                print(f"[REGISTRY] Parse error for {device_lower}: {e}")
        
        return None
    
    # Device not recognized
    return None


def parse_device_response(response_str, device):
    """
    Parse response from device in format: device:status[:key=value:key=value...]
    
    Example input: stepper:ok:position=45:calibrated=1:enabled=0
    Example output: {"s": "ok", "device": "stepper", "data": {"position": 45, "calibrated": 1, "enabled": 0}}
    
    Returns:
        Dictionary with parsed response or error
    """
    try:
        if not response_str:
            return {"s": "error", "msg": "empty_response"}
        
        # Verify device prefix
        if not response_str.startswith(f"{device}:"):
            return {"s": "error", "msg": f"wrong_device: {response_str}"}
        
        # Remove device prefix
        parts = response_str.split(":")
        if len(parts) < 2:
            return {"s": "error", "msg": "invalid_format"}
        
        # parts[0] = device name (already verified)
        # parts[1] = status (OK or error or other)
        status = parts[1].lower()
        
        # Parse KEY=VALUE pairs (parts[2:])
        data = {}
        for i in range(2, len(parts)):
            pair = parts[i]
            if "=" in pair:
                key, value = pair.split("=", 1)
                # Try to convert value to appropriate type
                try:
                    # Try int
                    data[key] = int(value)
                except ValueError:
                    try:
                        # Try float
                        data[key] = float(value)
                    except ValueError:
                        # Keep as string
                        data[key] = value
        
        # Check for success/error
        if status == "OK":
            return {
                "s": "ok",
                "device": device,
                "status": status,
                "data": data,
                "raw": response_str
            }
        elif status == "error":
            error_msg = data.get("msg") or data.get("error") or "Unknown error"
            return {
                "s": "error",
                "device": device,
                "status": status,
                "msg": error_msg,
                "data": data,
                "raw": response_str
            }
        else:
            return {
                "s": "ok",
                "device": device,
                "status": status,
                "data": data,
                "raw": response_str
            }
    
    except Exception as e:
        return {"s": "error", "msg": f"parse_error: {e}", "raw": response_str}


# ========== master status ENDPOINTS ==========
def master_ping():
    """GET: Master alive check"""
    return {"s": "ok", "msg": "Master ready", "type": "pico_master"}

def master_whoami():
    """GET: Master device identification"""
    return {"s": "ok", "device": "master", "type": "pico_master", "msg": "Pico Master Controller"}

def master_status():
    """GET: Master and slave status"""
    return {
        "s": "ok",
        "master": "ready",
        "slaves_configured": list(SLAVES.keys()),
        "uptime_ms": utime.ticks_ms(),
        "led": "on"
    }

def master_rediscover():
    """Reset device registry and perform discovery"""
    global device_commands, devices_initialized
    
    print("\n[REDISCOVERY] Resetting device registry and reconnecting...")
    
    # Reset registry (keep master)
    device_commands = {"master": ["ping", "status", "commands", "whoami", "rediscover", "scan", "force"]}
    devices_initialized = False
    
    # Perform discovery
    initialize_device_registry()
    
    return {
        "s": "ok",
        "msg": "Device rediscovery complete",
        "registry_initialized": devices_initialized,
        "discovered_devices": len(device_commands) - 1  # Exclude master
    }

def master_scan():
    """Scan network for any UART devices"""
    scan_result = network_scan()
    
    return {
        "s": "ok",
        "msg": "Network scan complete",
        "total_scanned": scan_result["total_scanned"],
        "total_found": scan_result["total_found"],
        "found_devices": scan_result["found_devices"]
    }

def master_force(device, cmd_with_args):
    """Force send any command without validation - for testing/debugging"""
    print(f"\n[FORCE] Sending raw command to {device}: {cmd_with_args}")
    
    resp = send_uart_command_raw(device, cmd_with_args, timeout_ms=5000)
    
    if resp:
        return {
            "s": "ok",
            "msg": "Force command successful",
            "device": device,
            "command": cmd_with_args,
            "response": resp
        }
    else:
        return {
            "s": "error",
            "msg": "Force command timeout - no response",
            "device": device,
            "command": cmd_with_args
        }

def process_command(line, source='uart'):
    """Process command from server and return response to server
    This function implements the request-response architecture:
    Server sends command -> Master processes -> Master sends to Slave -> 
    Slave responds -> Master receives -> Master sends response back to Server
    """
    try:
        if isinstance(line, bytes):
            line = line.decode().strip().lower()
        elif isinstance(line, str):
            line = line.strip().lower()
        else:
            line = str(line).strip().lower()
        
        if not line:
            return b''
        
        # Log source of request
        if source == 'uart':
            print(f"[SERVER-REQ] {line}")
        else:
            print(f"[USB-REQ] {line}")
        
        # Route command to appropriate endpoint
        response = None
        
        # ========== master commands ==========
        if line == 'master:ping' or line == 'ping':
            response = master_ping()
        elif line == 'master:rediscover' or line == 'rediscover':
            response = master_rediscover()
        elif line == 'master:scan' or line == 'scan':
            response = master_scan()
        elif line.startswith('master:force:') or line.startswith('force:'):
            # Extract force command: force:device:command[:args]
            if line.startswith('master:force:'):
                force_cmd = line[13:]  # Remove 'master:force:' prefix
            else:
                force_cmd = line[6:]  # Remove 'force:' prefix
            
            parts = force_cmd.split(':', 1)
            if len(parts) >= 2:
                device_name = parts[0].lower()
                cmd_with_args = parts[1]
                response = master_force(device_name, cmd_with_args)
            else:
                response = {
                    "s": "error",
                    "msg": "Force command format: force:device:command[:args]",
                    "example": "force:servo:open"
                }
        elif line == 'master:commands':
            # List all devices and their available commands
            commands_by_device = {
                "master": ["ping", "whoami", "status", "commands", "help", "rediscover", "scan", "force"]
            }
            if device_commands:
                # Add all slave device commands
                commands_by_device.update(device_commands)
            else:
                # If registry not initialized, show configured devices with empty lists
                for device in SLAVES.keys():
                    commands_by_device[device] = []
            
            response = {
                "s": "ok",
                "device": "master",
                "msg": "All available device commands",
                "commands": commands_by_device,
                "registry_initialized": devices_initialized,
                "total_devices": len(SLAVES),
                "discovered_devices": len(device_commands)
            }
        elif line == 'master:whoami' or line == 'whoami':
            response = master_whoami()
        elif line == 'master:status' or line == 'status':
            response = master_status()
        
        # ========== GENERIC DEVICE COMMAND ROUTER ==========
        # Handle any device:command[:args] format
        elif ':' in line:
            try:
                parts = line.split(':', 1)
                device_name = parts[0].lower()
                cmd_with_args = parts[1]
                
                # Allow devices that are discoverable or in registry (don't require them to be in SLAVES)
                if device_name not in DISCOVERABLE_DEVICES and device_name not in device_commands and device_name not in SLAVES:
                    response = {
                        "s": "error",
                        "msg": f"Unknown device: {device_name}",
                        "available_devices": list(set(DISCOVERABLE_DEVICES + list(device_commands.keys())))
                    }
                else:
                    # Get device's command list
                    cmd_list = get_device_commands(device_name)
                    
                    if cmd_list is None:
                        # Device not responding yet - try direct command anyway
                        print(f"[ROUTER] Device {device_name} not in registry, attempting direct command...")
                        resp = send_device_command(device_name, cmd_with_args)
                        if resp:
                            response = parse_device_response(resp, device_name)
                        else:
                            response = {
                                "s": "error",
                                "msg": f"Device {device_name} not responding",
                                "hint": "Device may not be powered on or connected"
                            }
                    else:
                        # Extract command name (before any colon or other parameters)
                        cmd_name = cmd_with_args.split(':')[0].split('=')[0].lower()
                        
                        # Check if command is supported
                        supported_commands = [c.lower() for c in cmd_list]
                        
                        if cmd_name not in supported_commands:
                            response = {
                                "s": "error",
                                "msg": f"Command '{cmd_name}' not supported by device {device_name}",
                                "available_commands": cmd_list
                            }
                        else:
                            # Send command to device
                            resp = send_device_command(device_name, cmd_with_args)
                            if resp:
                                response = parse_device_response(resp, device_name)
                            else:
                                response = {
                                    "s": "error",
                                    "msg": f"No response from device {device_name}",
                                    "hint": "Device may be busy or unresponsive"
                                }
            except Exception as e:
                print(f"[ROUTER] Error processing generic command: {e}")
                response = {
                    "s": "error",
                    "msg": f"Command processing error: {type(e).__name__}",
                    "details": str(e)
                }
        
        else:
            print(f"[UNKNOWN] Command not recognized: {line}")
            response = b'UNKNOWN\n'
        
        # Log and return response to server
        if response:
            print(f"[SERVER-RES] Sending response: {response}")
        return response
        
    except Exception as e:
        print(f"[master-ERR] Processing error: {e}")
        return b'error\n'

# ============ MAIN EVENT LOOP ============
# Implements full request-response architecture:
# Server (via UART) <-> Master (processes) <-> Slave (I2C or UART)
# Plus separate handling for Radar UART

print("=" * 70)
print("Master Pico I2C CRUD API - Request-Response Architecture")
print("=" * 70)
print("Server -> Master -> Slave -> Master -> Server")
print("Type 'HELP' for available commands")
print("=" * 70)

# Initialize device registry by querying all slaves for their commands
initialize_device_registry()

print("\n" + "=" * 70)
print("Master Ready - Waiting for server commands...")
print("=" * 70 + "\n")

while True:
    # ========== REQUEST FROM SERVER via UART ==========
    # Main communication channel: Server sends request, Master processes, responds
    led.on()  # Turn on LED while processing to indicate activity
    if uart_server.any():
        try:
            raw_line = uart_server.readline()
            line = raw_line.decode().strip() if isinstance(raw_line, bytes) else raw_line.strip()
            # Process command and get response
            resp = process_command(line, source='uart')
            # Send response back to server
            if resp:
                if isinstance(resp, dict):
                    # Convert dict to JSON string
                    import json
                    resp = json.dumps(resp).encode()
                elif isinstance(resp, str):
                    resp = resp.encode()
                uart_server.write(resp + b'\n')
                print(f"[UART-SENT] Response sent to server\n")
        except Exception as e:
            print(f"[UART-ERR] Failed to process server command: {e}")
            uart_server.write(b'error\n')

    # ========== REQUEST FROM USB SERIAL (for testing/debug) ==========
    # Secondary input for development/testing
    result = select.select([sys.stdin], [], [], 0)
    if result and result[0]:
        try:
            line = sys.stdin.readline()
            resp = process_command(line, source='usb')
            if resp and isinstance(resp, bytes):
                try:
                    decoded = resp.decode()
                    print(f"[USB-RES] {decoded}")
                except:
                    print(f"[USB-RES] {resp}")
            elif resp:
                print(f"[USB-RES] {resp}")
        except Exception as e:
            print(f"[USB-ERR] Failed to process USB command: {e}")

    # Keep LED on to show device is powered
    led.on()

    # Small delay to prevent CPU hogging
    sleep(0.01)
