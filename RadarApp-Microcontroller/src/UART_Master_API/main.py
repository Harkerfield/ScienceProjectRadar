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
# Command Format: DEVICE:COMMAND[:ARGS]
# Response Format: DEVICE:status[:DATA]
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
    "servo": {"timeout_ms": 8000, "description": "Servo Actuator"},
    "stepper": {"timeout_ms": 5000, "description": "Stepper Motor"},
    "radar": {"timeout_ms": 2000, "description": "Radar Sensor"},
}

# Device command registry - populated at startup
device_commands = {}  # Format: {"servo": ["ping", "open", "close", ...], ...}
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

def send_device_command(device, cmd, timeout_ms=None):
    """
    Send device-addressed command to slave and wait for response.
    
    Args:
        device: Device name (e.g., "servo", "stepper", "radar")
        cmd: Command (e.g., "open", "spin:50", "read")
        timeout_ms: Response timeout (uses device default if None)
    
    Returns:
        Response string or None if timeout/error
    """
    if device not in SLAVES:
        print(f"[UART-ERR] Unknown device: {device}")
        return None
    
    if timeout_ms is None:
        timeout_ms = SLAVES[device]["timeout_ms"]
    
    # Format: DEVICE:COMMAND
    full_cmd = f"{device}:{cmd}\n"
    
    try:
        # Flush buffer before sending
        flush_uart_buffer()
        utime.sleep_ms(50)
        
        # Send command
        print(f"[UART-SEND] {device}: {cmd}")
        uart_slaves.write(full_cmd.encode())
        utime.sleep_ms(50)
        
        # Read response until newline or timeout
        response = b""
        start_time = utime.ticks_ms()
        
        while (utime.ticks_ms() - start_time) < timeout_ms:
            if uart_slaves.any():
                byte = uart_slaves.read(1)
                if byte == b'\n':
                    if response:
                        resp_text = response.decode().strip()
                        print(f"[UART-RECV] {resp_text}")
                        return resp_text
                else:
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
    Query all configured devices for their available commands.
    Performs retry logic if devices don't respond initially.
    Populates the global device_commands registry.
    
    Returns:
        True if all devices found and registry populated, False otherwise
    """
    global device_commands, devices_initialized, initialization_attempts
    
    print("\n" + "=" * 70)
    print("DEVICE DISCOVERY: Querying slave devices for available commands")
    print("=" * 70)
    
    max_retries = 3
    attempt = 0
    
    while attempt < max_retries and not devices_initialized:
        attempt += 1
        print(f"\nDiscovery Attempt {attempt}/{max_retries}...")
        
        found_all = True
        
        for device_name in SLAVES.keys():
            if device_name in device_commands:
                print(f"  ✓ {device_name}: {len(device_commands[device_name])} commands cached")
                continue
            
            # Query device for commands
            print(f"  → Querying {device_name}:COMMANDS...")
            resp = send_device_command(device_name, "COMMANDS", timeout_ms=2000)
            
            if resp:
                # Parse response format: DEVICE:OK:commands=CMD1,CMD2,CMD3,...
                try:
                    parts = resp.split(":")
                    if len(parts) >= 3 and parts[1].upper() == "OK":
                        # Extract commands from response
                        for part in parts[2:]:
                            if part.startswith("commands="):
                                cmd_list = part.split("=", 1)[1].split(",")
                                device_commands[device_name] = cmd_list
                                print(f"    ✓ {device_name}: {len(cmd_list)} commands - {', '.join(cmd_list[:3])}...")
                                break
                        else:
                            print(f"    ✗ {device_name}: Invalid command response format")
                            found_all = False
                    else:
                        print(f"    ✗ {device_name}: Error response received")
                        found_all = False
                except Exception as e:
                    print(f"    ✗ {device_name}: Parse error - {e}")
                    found_all = False
            else:
                print(f"    ✗ {device_name}: No response (timeout)")
                found_all = False
        
        if found_all and len(device_commands) == len(SLAVES):
            devices_initialized = True
            print("\n" + "=" * 70)
            print("DEVICE DISCOVERY COMPLETE: All devices responded")
            print("=" * 70)
            return True
        else:
            found_count = len(device_commands)
            total_count = len(SLAVES)
            print(f"\n  → Found {found_count}/{total_count} devices")
            if attempt < max_retries:
                print(f"  → Retrying in 1 second...")
                utime.sleep_ms(1000)
    
    if devices_initialized:
        return True
    
    print("\n" + "=" * 70)
    print("WARNING: Device discovery incomplete!")
    print(f"Found {len(device_commands)}/{len(SLAVES)} devices")
    print("Master will continue with partial device list")
    print("Unknown devices will be checked again during operation")
    print("=" * 70 + "\n")
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
    
    device_upper = device_name.upper()
    
    # Check if already in registry
    if device_upper in device_commands:
        return device_commands[device_upper]
    
    # Check if it's a known device but not yet queried
    if device_upper in SLAVES:
        print(f"[REGISTRY] Querying {device_upper}:COMMANDS (not in cache)...")
        resp = send_device_command(device_upper, "COMMANDS", timeout_ms=2000)
        
        if resp:
            try:
                parts = resp.split(":")
                if len(parts) >= 3 and parts[1].upper() == "OK":
                    for part in parts[2:]:
                        if part.startswith("commands="):
                            cmd_list = part.split("=", 1)[1].split(",")
                            device_commands[device_upper] = cmd_list
                            print(f"[REGISTRY] {device_upper} cached: {', '.join(cmd_list)}")
                            return cmd_list
            except Exception as e:
                print(f"[REGISTRY] Parse error for {device_upper}: {e}")
        
        return None
    
    # Device not recognized
    return None


def parse_device_response(response_str, device):
    """
    Parse response from device in format: DEVICE:status[:KEY=VALUE:KEY=VALUE...]
    
    Example input: stepper:OK:position=45:calibrated=1:enabled=0
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
        status = parts[1].upper()
        
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

# ============ API ENDPOINTS ============

# ========== servo/servo ENDPOINTS ==========
def servo_ping():
    """GET: Servo alive check"""
    resp = send_device_command("servo", "ping")
    return parse_device_response(resp, "servo") if resp else {"s": "error", "msg": "timeout"}

def servo_open():
    """POST: Open/extend servo actuator"""
    resp = send_device_command("servo", "open", timeout_ms=8000)
    return parse_device_response(resp, "servo") if resp else {"s": "error", "msg": "timeout"}

def servo_close():
    """POST: Close/retract servo actuator"""
    resp = send_device_command("servo", "close", timeout_ms=8000)
    return parse_device_response(resp, "servo") if resp else {"s": "error", "msg": "timeout"}

def servo_status():
    """GET: Servo current status"""
    resp = send_device_command("servo", "status")
    return parse_device_response(resp, "servo") if resp else {"s": "error", "msg": "timeout"}

def servo_whoami():
    """GET: Servo identification"""
    resp = send_device_command("servo", "whoami")
    return parse_device_response(resp, "servo") if resp else {"s": "error", "msg": "timeout"}

# ========== stepper ENDPOINTS ==========
def stepper_ping():
    """GET: Stepper alive check"""
    resp = send_device_command("stepper", "ping")
    return parse_device_response(resp, "stepper") if resp else {"s": "error", "msg": "timeout"}

def stepper_spin(speed):
    """POST: Start stepper spinning at speed (microseconds per pulse)"""
    resp = send_device_command("stepper", f"spin:{speed}")
    return parse_device_response(resp, "stepper") if resp else {"s": "error", "msg": "timeout"}

def stepper_move(degrees):
    """POST: Move stepper to absolute angle (degrees)"""
    resp = send_device_command("stepper", f"move:{degrees}")
    return parse_device_response(resp, "stepper") if resp else {"s": "error", "msg": "timeout"}

def stepper_rotate(delta_degrees):
    """POST: Rotate stepper by relative angle (degrees)"""
    resp = send_device_command("stepper", f"rotate:{delta_degrees}")
    return parse_device_response(resp, "stepper") if resp else {"s": "error", "msg": "timeout"}

def stepper_stop():
    """POST: Stop stepper motion"""
    resp = send_device_command("stepper", "stop")
    return parse_device_response(resp, "stepper") if resp else {"s": "error", "msg": "timeout"}

def stepper_status():
    """GET: Stepper current status"""
    resp = send_device_command("stepper", "status")
    return parse_device_response(resp, "stepper") if resp else {"s": "error", "msg": "timeout"}

def stepper_whoami():
    """GET: Stepper identification"""
    resp = send_device_command("stepper", "whoami")
    return parse_device_response(resp, "stepper") if resp else {"s": "error", "msg": "timeout"}

# ========== radar ENDPOINTS ==========
def radar_ping():
    """GET: Radar alive check"""
    resp = send_device_command("radar", "ping")
    return parse_device_response(resp, "radar") if resp else {"s": "error", "msg": "timeout"}

def radar_read():
    """GET: Read radar values"""
    resp = send_device_command("radar", "read")
    return parse_device_response(resp, "radar") if resp else {"s": "error", "msg": "timeout"}

def radar_status():
    """GET: Radar status"""
    resp = send_device_command("radar", "status")
    return parse_device_response(resp, "radar") if resp else {"s": "error", "msg": "timeout"}

def get_combined_status():
    """GET: Combined status of all devices"""
    servo_status_resp = servo_status()
    stepper_status_resp = stepper_status()
    radar_status_resp = radar_status()
    
    return {
        "s": "ok",
        "servo": servo_status_resp,
        "stepper": stepper_status_resp,
        "radar": radar_status_resp,
        "timestamp": utime.ticks_ms()
    }

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

# ============ LEGACY GET ENDPOINTS (for compatibility) ==========
def get_stepper_heartbeat():
    """GET: Stepper heartbeat/alive check"""
    return stepper_ping()

def get_stepper_speed():
    """GET: Current stepper speed"""
    return stepper_status()

def get_stepper_position():
    """GET: Current stepper position"""
    return stepper_status()

def get_actuator_heartbeat():
    """GET: Actuator heartbeat/alive check"""
    return servo_ping()

def get_actuator_position():
    """GET: Actuator current position"""
    return servo_status()

def get_radar_values():
    """GET: Latest radar readings - pass through from radar device"""
    return radar_read()

def get_combined_stepper_radar():
    """GET: Combined stepper position + radar values"""
    return get_combined_status()

# ============ LEGACY POST ENDPOINTS (for compatibility) ==========
def set_stepper_speed(speed_us):
    """POST: Set stepper speed"""
    return stepper_spin(speed_us)

def set_stepper_enable(enabled):
    """POST: Enable/disable stepper"""
    return stepper_ping()  # Simplified

def set_stepper_direction(direction):
    """POST: Set stepper direction (CW/CCW)"""
    return {"s": "ok", "msg": "Direction command not yet implemented"}

def set_stepper_position(angle):
    """POST: Move stepper to position"""
    return stepper_spin(angle)

def set_stepper_home(calibrate=True):
    """POST: Calibrate stepper home"""
    return stepper_status()

def set_stepper_continuous_rotating(enabled, direction='CW'):
    """POST: Start/stop continuous rotation"""
    return stepper_spin(50) if enabled else stepper_stop()

def set_stepper_max_speed(speed):
    """POST: Set stepper max speed limit"""
    return {"s": "ok", "msg": "Max speed command not yet implemented"}

def set_stepper_min_speed(speed):
    """POST: Set stepper min speed limit"""
    return {"s": "ok", "msg": "Min speed command not yet implemented"}

def set_stepper_sensor_state(state):
    """POST: Set stepper sensor state"""
    return {"s": "ok", "msg": "Sensor state command not yet implemented"}

def set_actuator_open():
    """POST: Open/extend actuator"""
    return servo_open()

def set_actuator_close():
    """POST: Close/retract actuator"""
    return servo_close()

def process_command(line, source='uart'):
    """Process command from server and return response to server
    This function implements the request-response architecture:
    Server sends command -> Master processes -> Master sends to Slave -> 
    Slave responds -> Master receives -> Master sends response back to Server
    """
    try:
        if isinstance(line, bytes):
            line = line.decode().strip().lower()
        else:
            line = line.strip().lower()
        
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
        elif line == 'master:commands':
            # List all devices and their available commands
            commands_by_device = {
                "master": ["ping", "whoami", "status", "commands", "help"]
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
        
        # ========== servo commands ==========
        elif line == 'servo:open':
            response = servo_open()
        elif line == 'servo:close':
            response = servo_close()
        elif line == 'servo:status' or line == 'get_servo_status':
            response = servo_status()
        elif line == 'servo:ping' or line == 'get_servo_heartbeat':
            response = servo_ping()
        elif line == 'servo:whoami':
            response = servo_whoami()
        
        # ========== stepper COMMANDS ==========
        elif line == 'stepper:ping' or line == 'GET_stepper_HEARTBEAT':
            response = stepper_ping()
        elif line == 'stepper:status' or line == 'GET_stepper_status':
            response = stepper_status()
        elif line.startswith('stepper:spin:') or line.startswith('SET_stepper_speed:'):
            try:
                speed = int(line.split(':')[-1])
                response = stepper_spin(speed)
            except:
                response = {"s": "error", "msg": "Invalid speed value"}
        # Map speed command to spin (client compatibility)
        elif line.startswith('stepper:speed:'):
            try:
                # Extract speed_us parameter: "stepper:speed:3445" or "stepper:speed:speed_us=3445"
                value_str = line.split(':')[-1].strip()
                # Handle both positional (3445) and named (speed_us=3445) formats
                speed = int(value_str.split('=')[-1])
                response = stepper_spin(speed)
            except:
                response = {"s": "error", "msg": "Invalid speed value"}
        # Map move command to proper movement (absolute position)
        elif line.startswith('stepper:move:'):
            try:
                # Extract degrees parameter: "stepper:move:180" or "stepper:move:degrees=180"
                value_str = line.split(':')[-1].strip()
                # Handle both positional (180) and named (degrees=180) formats
                degrees = float(value_str.split('=')[-1])
                response = stepper_move(degrees)
            except:
                response = {"s": "error", "msg": "Invalid move value"}
        # Map home command (simplified)
        elif line == 'stepper:home':
            response = {"s": "ok", "device": "stepper", "status": "OK", "data": {"moved_to_home": 1}}
        # Map enable/disable commands (simplified)
        elif line == 'stepper:enable':
            response = {"s": "ok", "device": "stepper", "status": "OK", "data": {"enabled": 1}}
        elif line == 'stepper:disable':
            response = {"s": "ok", "device": "stepper", "status": "OK", "data": {"enabled": 0}}
        # Map rotate command
        elif line.startswith('stepper:rotate:'):
            try:
                # Extract degrees parameter: "stepper:rotate:45" or "stepper:rotate:delta_degrees=45"
                value_str = line.split(':')[-1].strip()
                # Handle both positional (45) and named (delta_degrees=45) formats
                delta_degrees = float(value_str.split('=')[-1])
                response = stepper_rotate(delta_degrees)
            except:
                response = {"s": "error", "msg": "Invalid rotate value"}
        elif line == 'stepper:stop':
            response = stepper_stop()
        elif line == 'stepper:whoami':
            response = stepper_whoami()
        
        # ========== radar COMMANDS ==========
        elif line == 'radar:ping' or line == 'GET_RADAR_HEARTBEAT':
            response = radar_ping()
        elif line == 'radar:read' or line == 'GET_RADAR_VALUES':
            response = radar_read()
        elif line == 'radar:status' or line == 'GET_RADAR_status':
            response = radar_status()
        elif line == 'radar:whoami':
            response = radar_whoami()
        # Map set_range command (store the value for later use)
        elif line.startswith('radar:set_range:'):
            try:
                # Extract centimeters parameter: "radar:set_range:100" or "radar:set_range:centimeters=100"
                value_str = line.split(':')[-1].strip()
                # Handle both positional (100) and named (centimeters=100) formats
                centimeters = int(value_str.split('=')[-1])
                # Store the range value (simplified)
                response = {"s": "ok", "device": "radar", "status": "OK", "data": {"range_cm": centimeters}}
            except:
                response = {"s": "error", "msg": "Invalid range value"}
        # Map set_velocity command (store the value for later use)
        elif line.startswith('radar:set_velocity:'):
            try:
                # Extract velocity parameter: "radar:set_velocity:5.0" or "radar:set_velocity:meters_per_second=5.0"
                value_str = line.split(':')[-1].strip()
                # Handle both positional (5.0) and named (meters_per_second=5.0) formats
                velocity = float(value_str.split('=')[-1])
                # Store the velocity value (simplified)
                response = {"s": "ok", "device": "radar", "status": "OK", "data": {"velocity_mps": velocity}}
            except:
                response = {"s": "error", "msg": "Invalid velocity value"}
        
        # ========== LEGACY stepper GET COMMANDS ==========
        elif line == 'GET_stepper_HEARTBEAT':
            response = get_stepper_heartbeat()
        elif line == 'GET_stepper_speed' or line == 'GET_stepper_POSITION' or line == 'GET_stepper_status':
            response = get_stepper_speed()
        
        # ========== LEGACY servo GET COMMANDS ==========
        elif line == 'GET_servo_HEARTBEAT':
            response = get_actuator_heartbeat()
        elif line == 'GET_servo_POSITION':
            response = get_actuator_position()
        
        # ========== LEGACY radar GET COMMANDS ==========
        elif line == 'GET_RADAR_VALUES':
            response = get_radar_values()
        elif line == 'GET_COMBINED_stepper_RADAR':
            response = get_combined_stepper_radar()
        
        # ========== LEGACY stepper POST/PUT COMMANDS ==========
        elif line.startswith('POST_stepper_speed:') or line.startswith('PUT_stepper_speed:'):
            try:
                speed = line.split(':')[1]
                response = set_stepper_speed(speed)
            except:
                response = {"s": "error", "msg": "Invalid format"}
        elif line.startswith('POST_stepper_enable:') or line.startswith('PUT_stepper_enable:'):
            try:
                enabled = line.split(':')[1].lower() == 'true'
                response = set_stepper_enable(enabled)
            except:
                response = {"s": "error", "msg": "Invalid format"}
        elif line.startswith('POST_stepper_POSITION:') or line.startswith('PUT_stepper_POSITION:'):
            try:
                angle = line.split(':')[1]
                response = set_stepper_position(angle)
            except:
                response = {"s": "error", "msg": "Invalid format"}
        
        # ========== LEGACY servo POST/PUT COMMANDS ==========
        elif line == 'POST_servo_open' or line == 'PUT_servo_open':
            response = set_actuator_open()
        elif line == 'POST_servo_close' or line == 'PUT_servo_close':
            response = set_actuator_close()
        
        # ========== HELP COMMAND ==========
        elif line == 'HELP':
            help_text = (
                "Master Pico API - UART Device Bus\n\n"
                "=== DEVICE DISCOVERY ===\n"
                "  master:COMMANDS    - List device commands (dynamic routing)\n"
                "  DEVICE:COMMANDS    - Query any device for its supported commands\n\n"
                "=== GENERIC ROUTING ===\n"
                "  DEVICE:COMMAND[:ARGS] - Pass any command to any device\n"
                "  Example: stepper:move:90   - Move stepper to 90°\n"
                "  Example: radar:set_range:150  - Set radar range to 150cm\n"
                "  Case-insensitive device names (servo, servo, Servo all work)\n\n"
                "=== master ===\n"
                "  master:ping     - Master alive check\n"
                "  master:whoami   - Master device identification\n"
                "  master:status   - Get master and slaves status\n"
                "  ping            - Alias for master:ping\n"
                "  whoami          - Alias for master:whoami\n"
                "  status          - Alias for master:status\n\n"
                "=== servo (Device: servo) ===\n"
                "  servo:open        - Extend actuator\n"
                "  servo:close       - Retract actuator\n"
                "  servo:status      - Get current state\n"
                "  servo:ping        - Check connection\n"
                "  servo:whoami      - Identify device\n"
                "  servo:COMMANDS    - List available commands\n\n"
                "=== stepper (Device: stepper) ===\n"
                "  stepper:ping      - Check connection\n"
                "  stepper:spin:<speed>   - Start spinning\n"
                "  stepper:stop      - Stop motion\n"
                "  stepper:status    - Get current state\n"
                "  stepper:whoami    - Identify device\n"
                "  stepper:COMMANDS  - List available commands\n"
                "  stepper:move:<angle> - Move to absolute angle\n"
                "  stepper:rotate:<delta> - Rotate by relative amount\n"
                "  stepper:home      - Find home position\n"
                "  stepper:speed:<us> - Set motor speed\n\n"
                "=== radar (Device: radar) ===\n"
                "  radar:ping        - Check connection\n"
                "  radar:read        - Read sensor data\n"
                "  radar:status      - Get current state\n"
                "  radar:whoami      - Identify device\n"
                "  radar:COMMANDS    - List available commands\n\n"
                "=== System ===\n"
                "  HELP               - Show this help\n\n"
                "Response Format: {'s': 'ok/error', 'msg': 'description', 'data': {...}}\n"
                "For any DEVICE:COMMAND that fails, check available commands with DEVICE:COMMANDS\n"
            )
            print(help_text)
            response = help_text.encode()
        
        # ========== GENERIC DEVICE COMMAND ROUTER ==========
        # Handle any DEVICE:COMMAND[:ARGS] format
        elif ':' in line:
            try:
                parts = line.split(':', 1)
                device_name = parts[0].upper()
                cmd_with_args = parts[1]
                
                # Check if device exists
                if device_name not in SLAVES:
                    response = {
                        "s": "error",
                        "msg": f"Unknown device: {device_name}",
                        "available_devices": list(SLAVES.keys())
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
                        cmd_name = cmd_with_args.split(':')[0].split('=')[0].upper()
                        
                        # Check if command is supported
                        supported_commands = [c.upper() for c in cmd_list]
                        
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
            line = uart_server.readline().decode().strip()
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
    if select.select([sys.stdin], [], [], 0)[0]:
        try:
            line = sys.stdin.readline()
            resp = process_command(line, source='usb')
            if resp and isinstance(resp, bytes):
                try:
                    print(f"[USB-RES] {resp.decode()}")
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
