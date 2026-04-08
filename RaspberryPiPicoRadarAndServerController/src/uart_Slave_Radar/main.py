# MicroPython UART Slave - Radar Sensor Controller
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
# UART Slave (on shared UART1 bus with device addressing)
# Command Format: RADAR:COMMAND[:ARGS]
# Response Format: RADAR:STATUS[:DATA]
# Commands: PING, STATUS, WHOAMI, READ

from machine import UART, Pin
import utime
import sys
import select

# Display MicroPython version
print("=" * 50)
print(f"MicroPython Version: {sys.version}")
print(f"MicroPython Implementation: {sys.implementation}")
print("=" * 50)


# Disable WiFi/Bluetooth to avoid CYW43 interference
try:
    import network
    network.country('US')  # Set country first
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    print("[OK] WiFi disabled")
except Exception as e:
    print(f"[WARN] WiFi disable failed: {e}")

# LED for activity indication
led = Pin("LED", Pin.OUT)
led.on()
print("[INIT] LED turned ON")

# ============================================================
# UART CONFIGURATION
# ============================================================
# UART1: Slave communication bus (shared with SERVO and STEPPER)
uart_slaves = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
print("[STARTUP] UART slave initialized (TX=GPIO4, RX=GPIO5)")

# ============ DEVICE IDENTIFICATION ============
DEVICE_NAME = "RADAR"
DEVICE_ADDR = 0x20     # Virtual device address for UART bus

# Sensor simulation data
radar_range = 123      # Distance in cm
radar_velocity = 4.5   # Velocity in m/s

print(f"[STARTUP] Radar sensor initialized")
print(f"[STARTUP] Initial range: {radar_range}cm, velocity: {radar_velocity}m/s")

# ============ UART COMMUNICATION LAYER ============

def flush_uart_buffer():
    """Clear any stale data in UART buffer"""
    while uart_slaves.any():
        uart_slaves.read()
    utime.sleep_ms(50)

def send_uart_response(status_msg):
    """
    Send device-addressed response via UART.
    Format: RADAR:OK:key=val:key=val\n
    
    Args:
        status_msg: Status message (e.g., "OK:range=123" or "ERROR:invalid_command")
    """
    response = f"{DEVICE_NAME}:{status_msg}\n"
    uart_slaves.write(response.encode())
    print(f"[UART-SEND] {response.strip()}")
    return response

def process_usb_command_old(line):
    """Legacy USB command processing - DEPRECATED"""
    pass

def process_uart_command(cmd_text):
    """Process UART command received from master.
    Format: RADAR:COMMAND[:ARGS]
    Response: RADAR:STATUS[:DATA]
    
    Supports commands: PING, STATUS, WHOAMI, READ
    """
    global radar_range, radar_velocity
    
    try:
        if not cmd_text:
            send_uart_response("ERROR:empty_command")
            return
        
        # Parse command format: RADAR:COMMAND[:ARGS]
        parts = cmd_text.strip().split(":", 2)  # Split on first 2 colons only
        
        if len(parts) < 2:
            send_uart_response("ERROR:invalid_format")
            return
        
        device = parts[0].upper()
        if device != DEVICE_NAME:
            send_uart_response(f"ERROR:wrong_device:{device}")
            return
        
        cmd = parts[1].upper()
        args = parts[2] if len(parts) > 2 else ""
        
        print(f"[UART-CMD] Device: {device}, Command: {cmd}, Args: {args}")
        
        # ========== STANDARD COMMANDS ==========
        if cmd == "PING":
            send_uart_response(f"OK:msg=alive:addr=0x{DEVICE_ADDR:02x}")
        
        elif cmd == "WHOAMI":
            send_uart_response(f"OK:device=RADAR:type=distance_sensor")
        
        elif cmd == "STATUS":
            # Calculate confidence based on distance (simulate signal strength)
            if radar_range > 0:
                confidence = min(100, max(20, 100 - (radar_range / 50)))
            else:
                confidence = 0
            
            movement = 1 if radar_velocity > 0.5 else 0
            send_uart_response(f"OK:range={radar_range}:velocity={radar_velocity}:confidence={int(confidence)}:movement={movement}")
        
        elif cmd == "READ":
            # Calculate confidence based on distance
            if radar_range > 0:
                confidence = min(100, max(20, 100 - (radar_range / 50)))
            else:
                confidence = 0
            
            movement = 1 if radar_velocity > 0.5 else 0
            send_uart_response(f"OK:range={radar_range}:velocity={radar_velocity:.1f}:confidence={int(confidence)}:movement={movement}")
        
        elif cmd == "SET_RANGE":
            # Command format: RADAR:SET_RANGE:value
            global radar_range
            try:
                radar_range = int(args) if args else radar_range
                send_uart_response(f"OK:range_set:value={radar_range}")
            except:
                send_uart_response(f"ERROR:invalid_range")
        
        elif cmd == "SET_VELOCITY":
            # Command format: RADAR:SET_VELOCITY:value
            global radar_velocity
            try:
                radar_velocity = float(args) if args else radar_velocity
                send_uart_response(f"OK:velocity_set:value={radar_velocity:.1f}")
            except:
                send_uart_response(f"ERROR:invalid_velocity")
        
        else:
            send_uart_response(f"ERROR:unknown_command:{cmd}")
    
    except Exception as e:
        print(f"[UART-ERR] Command processing error: {type(e).__name__}: {e}")
        send_uart_response(f"ERROR:command_error:{str(e)[:30]}")

def json_response(status, **kwargs):
    """Create minimal JSON response string - DEPRECATED for USB commands"""
    items = [f'"s":"{status}"']
    for k, v in kwargs.items():
        if isinstance(v, str):
            items.append(f'"{k}":"{v}"')
        else:
            items.append(f'"{k}":{v}')
    return "{" + ",".join(items) + "}"

def process_usb_command(line):
    """Process USB serial command - Legacy JSON format"""
    global radar_range, radar_velocity
    try:
        cmd = line.strip().upper()
        print(f"[USB] Received: {cmd}")
        if cmd.startswith('RANGE:'):
            radar_range = int(cmd.split(':')[1])
            return json_response("ok", msg="range_set", range=radar_range, vel=radar_velocity)
        elif cmd.startswith('VEL:'):
            radar_velocity = float(cmd.split(':')[1])
            return json_response("ok", msg="vel_set", range=radar_range, vel=radar_velocity)
        elif cmd == 'READ':
            return json_response("ok", range=radar_range, vel=radar_velocity)
        elif cmd == 'STATUS':
            return json_response("ok", msg="operational", range=radar_range, vel=radar_velocity)
        elif cmd == 'PING':
            return json_response("ok", msg="alive", addr=DEVICE_ADDR)
        elif cmd == 'WHOAMI':
            return json_response("ok", device="radar", addr=DEVICE_ADDR, type="distance_sensor")
        elif cmd == 'HELP':
            return "Commands: RANGE:<cm>|VEL:<m/s>|READ|STATUS|PING|WHOAMI|HELP"
        else:
            return json_response("error", msg="unknown_command")
    except Exception as e:
        return json_response("error", msg="command_error")

print("=" * 50)
print("Radar Pico Firmware Loaded Successfully!")
print("=" * 50)
print(f"[READY] Radar UART Slave ({DEVICE_NAME}) initialized")
print("[LED] Status indicator enabled on pin 25")
print("[UART] Listening for commands from Master Pico on UART1")
print("=" * 50)
print()
print("UART Protocol (shared bus with STEPPER and SERVO):")
print("  Format: RADAR:COMMAND[:ARGS]")
print("  Response: RADAR:STATUS[:DATA]")
print()
print("Available Commands:")
print("  PING           - Alive check")
print("  STATUS         - Get radar status (range, velocity, confidence, movement)")
print("  WHOAMI         - Device identification")
print("  READ           - Read current radar values")
print()
print("Examples:")
print("  RADAR:PING")
print("  RADAR:READ")
print("  RADAR:STATUS")
print("=" * 50)
print()

# Main loop
uart_buffer = b""  # Buffer for reading UART data command
loop_count = 0

print("[INIT] Starting main loop...")
print()

while True:
    loop_count += 1
    
    # Blink LED slowly to show we're alive
    if loop_count % 100 == 0:
        led.off()
    elif loop_count % 50 == 0:
        led.on()
    
    # Check for incoming UART data (commands from master)
    while uart_slaves.any():
        byte = uart_slaves.read(1)
        if byte == b'\n':
            # Complete command received
            cmd_text = uart_buffer.decode().strip()
            uart_buffer = b""
            
            if cmd_text:
                print(f"[UART-RECV] {cmd_text}")
                process_uart_command(cmd_text)
        else:
            uart_buffer += byte
            # Prevent buffer overflow
            if len(uart_buffer) > 256:
                uart_buffer = b""
                send_uart_response("ERROR:buffer_overflow")
    
    utime.sleep_ms(100)
