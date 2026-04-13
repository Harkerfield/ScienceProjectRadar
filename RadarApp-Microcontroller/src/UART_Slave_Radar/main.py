#v.Final J. 2026-04-13
# # MicroPython UART Slave - Radar Sensor Controller
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
# UART Slave (on shared UART1 bus with device addressing)
# 
# Command Format: radar:COMMAND[:ARGS]
# Response Format: radar:status[:DATA]
#
# Available Commands:
#   ping              - Alive check (responds with address)
#   whoami            - Device identification
#   status            - Get current sensor readings
#   read              - Get current sensor readings (alias for status)
#   set_range:<cm>    - Set distance reading (0-500 cm)
#   set_velocity:<m/s>- Set velocity reading (0.0-50.0 m/s)

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
# PIN DEFINITIONS
# ============================================================
UART_TX_PIN = 4
UART_RX_PIN = 5

# ============================================================
# UART CONFIGURATION
# ============================================================
# UART1: Slave communication bus (shared with servo and stepper)
uart_slaves = UART(1, baudrate=115200, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
print(f"[STARTUP] UART slave initialized (TX=GPIO{UART_TX_PIN}, RX=GPIO{UART_RX_PIN})")

# ============ DEVICE IDENTIFICATION ============
device_name = "radar"

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
    Format: radar:OK:key=val:key=val\n
    
    Args:
        status_msg: Status message (e.g., "OK:range=123" or "error:invalid_command")
    """
    response = f"{device_name}:{status_msg}\n"
    uart_slaves.write(response.encode())
    print(f"[UART-SEND] {response.strip()}")
    return response

def process_usb_command_old(line):
    """Legacy USB command processing - DEPRECATED"""
    pass

def process_uart_command(cmd_text):
    """Process UART command received from master.
    Format: radar:COMMAND[:ARGS]
    Response: radar:status[:DATA]
    
    Supports commands: ping, status, whoami, read
    """
    global radar_range, radar_velocity
    
    try:
        if not cmd_text:
            send_uart_response("error:empty_command")
            return
        
        # Parse command format: radar:COMMAND[:ARGS]
        parts = cmd_text.strip().split(":", 2)  # Split on first 2 colons only
        
        if len(parts) < 2:
            send_uart_response("error:invalid_format")
            return
        
        device = parts[0].lower()
        if device != device_name:
            send_uart_response(f"error:wrong_device:{device}")
            return
        
        cmd = parts[1].lower()
        args = parts[2] if len(parts) > 2 else ""
        
        print(f"[UART-CMD] Device: {device}, Command: {cmd}, Args: {args}")
        
        # ========== STANDARD COMMANDS ==========
        if cmd == "commands":
            commands = "ping,whoami,status,read,set_range,set_velocity"
            send_uart_response(f"ok:commands={commands}")
        
        elif cmd == "ping":
            send_uart_response(f"ok:msg=alive")
        
        elif cmd == "whoami":
            send_uart_response(f"ok:device=radar:type=distance_sensor")
        
        elif cmd == "status":
            # Calculate confidence based on distance (simulate signal strength)
            if radar_range > 0:
                confidence = min(100, max(20, 100 - (radar_range / 50)))
            else:
                confidence = 0
            
            movement = 1 if radar_velocity > 0.5 else 0
            send_uart_response(f"ok:range={radar_range}:velocity={radar_velocity}:confidence={int(confidence)}:movement={movement}")
        
        elif cmd == "read":
            # Calculate confidence based on distance
            if radar_range > 0:
                confidence = min(100, max(20, 100 - (radar_range / 50)))
            else:
                confidence = 0
            
            movement = 1 if radar_velocity > 0.5 else 0
            send_uart_response(f"ok:range={radar_range}:velocity={radar_velocity:.1f}:confidence={int(confidence)}:movement={movement}")
        
        elif cmd == "set_range":
            # Command format: radar:set_range:centimeters
            global radar_range
            try:
                if args:
                    radar_range = int(args)
                send_uart_response(f"ok:msg=range_set:range={radar_range}")
            except:
                send_uart_response(f"error:invalid_range")
        
        elif cmd == "set_velocity":
            # Command format: radar:set_velocity:meters_per_second
            global radar_velocity
            try:
                if args:
                    radar_velocity = float(args)
                send_uart_response(f"ok:msg=velocity_set:velocity={radar_velocity:.1f}")
            except:
                send_uart_response(f"error:invalid_velocity")
        
        else:
            send_uart_response(f"error:unknown_command:{cmd}")
    
    except Exception as e:
        print(f"[UART-ERR] Command processing error: {type(e).__name__}: {e}")
        send_uart_response(f"error:command_error:{str(e)[:30]}")

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
        cmd = line.strip().lower()
        print(f"[USB] Received: {cmd}")
        if cmd.startswith('RANGE:'):
            radar_range = int(cmd.split(':')[1])
            return json_response("ok", msg="range_set", range=radar_range, vel=radar_velocity)
        elif cmd.startswith('VEL:'):
            radar_velocity = float(cmd.split(':')[1])
            return json_response("ok", msg="vel_set", range=radar_range, vel=radar_velocity)
        elif cmd == 'read':
            return json_response("ok", range=radar_range, vel=radar_velocity)
        elif cmd == 'status':
            return json_response("ok", msg="operational", range=radar_range, vel=radar_velocity)
        elif cmd == 'ping':
            return json_response("ok", msg="alive")
        elif cmd == 'whoami':
            return json_response("ok", device="radar", type="distance_sensor")
        elif cmd == 'HELP':
            return "Commands: RANGE:<cm>|VEL:<m/s>|read|status|ping|whoami|HELP"
        else:
            return json_response("error", msg="unknown_command")
    except Exception as e:
        return json_response("error", msg="command_error")

print("=" * 70)
print("Radar Pico Firmware Loaded Successfully!")
print("=" * 70)
print(f"[readY] Radar UART Slave ({device_name}) initialized")
print(f"[PINS] UART TX=GPIO{UART_TX_PIN}, RX=GPIO{UART_RX_PIN}")
print("[LED] Status indicator enabled on pin 25")
print("[UART] Listening for commands from Master Pico on UART1")
print("=" * 70)
print()
print("UART Protocol (shared bus with stepper and servo):")
print("  Format: radar:COMMAND[:ARGS]")
print("  Response: radar:status[:DATA]")
print()
print("Available Commands:")
print()
print("  Read Commands:")
print("    ping           - Alive check, returns device address")
print("    whoami         - Device identification (name, type)")
print("    status         - Get radar status (range, velocity, confidence, movement)")
print("    read           - Read current radar values")
print()
print("  Write Commands:")
print("    set_range:<cm> - Set distance reading (e.g., set_range:250)")
print("    set_velocity:<m/s> - Set velocity reading (e.g., set_velocity:8.5)")
print()
print("Response Fields:")
print("    range          - Distance in centimeters (0-500)")
print("    velocity       - Speed in m/s (0.0-50.0)")
print("    confidence     - Signal confidence 0-100%")
print("    movement       - Movement detected (0 or 1)")
print()
print("Examples:")
print("  radar:ping")
print("  radar:read")
print("  radar:status")
print("  radar:set_range:300")
print("  radar:set_velocity:6.2")
print("=" * 70)
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
                send_uart_response("error:buffer_overflow")
    
    utime.sleep_ms(100)
