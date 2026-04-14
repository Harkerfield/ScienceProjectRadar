# v.Final J. 2026-04-13
# Radar sensor controller code for Raspberry Pi Pico using MicroPython
# # MicroPython UART Slave - Radar Sensor Controller
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
# UART Slave (on shared UART1 bus with device addressing)
# 
# Command Format: radar:command[:args]
# Response Format: radar:status[:data]
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

# ============ SUPPORTED COMMANDS ============
SUPPORTED_COMMANDS = ["ping", "whoami", "status", "read", "set_range", "set_velocity"]

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
    # Small delay to let master clear its RX buffer after command transmission
    utime.sleep_ms(50)
    
    response = f"{device_name}:{status_msg}\n"
    uart_slaves.write(response.encode())
    utime.sleep_ms(10)  # Allow buffer to flush on shared UART bus
    print(f"[UART-SEND] {response.strip()}")
    return response

def process_command(cmd_text, source="unknown"):
    """Process command from either UART or USB/REPL.
    Format: radar:command[:args]
    Sends response via send_uart_response
    """
    global radar_range, radar_velocity
    
    try:
        cmd_text = cmd_text.strip().lower()
        if not cmd_text:
            return
        
        print(f"[CMD-{source.lower()}] {cmd_text}")
        
        # Parse command format: radar:command[:args]
        parts = cmd_text.split(":", 2)
        
        if len(parts) < 2:
            # Handle legacy format: just "read" -> auto-prefix with device
            parts = [device_name, parts[0]]
        
        device = parts[0].lower()
        if device != device_name:
            # Silently ignore commands not for this device on UART (shared bus)
            # Only respond to errors if from USB/REPL
            if source == "usb":
                send_uart_response(f"error:wrong_device:{device}")
            return
        
        cmd = parts[1].lower()
        args = parts[2] if len(parts) > 2 else ""
        
        # ========== STANDARD COMMANDS ==========
        if cmd == "commands":
            send_uart_response(f"ok:commands={','.join(SUPPORTED_COMMANDS)}")
        
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
            if args:
                try:
                    radar_range = int(args)
                    send_uart_response(f"ok:msg=range_set:range={radar_range}")
                except:
                    send_uart_response(f"error:invalid_range:{args}")
            else:
                send_uart_response(f"error:missing_range_value")
        
        elif cmd == "set_velocity":
            if args:
                try:
                    radar_velocity = float(args)
                    send_uart_response(f"ok:msg=velocity_set:velocity={radar_velocity:.1f}")
                except:
                    send_uart_response(f"error:invalid_velocity:{args}")
            else:
                send_uart_response(f"error:missing_velocity_value")
        
        else:
            send_uart_response(f"error:unknown_command:{cmd}")
    
    except Exception as e:
        print(f"[CMD-ERR] Processing error: {type(e).__name__}: {e}")
        send_uart_response(f"error:command_error:{str(e)[:30]}")

def process_uart_command(cmd_text):
    """Deprecated wrapper - routes to unified process_command"""
    process_command(cmd_text, source="uart")

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
print("  Format: radar:command[:args]")
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
        if not byte:
            continue
        if byte == b'\n':
            # Complete command received
            cmd_text = uart_buffer.decode().strip()
            uart_buffer = b""
            
            if cmd_text:
                print(f"[UART-RECV] {cmd_text}")
                process_command(cmd_text, source="uart")
        else:
            uart_buffer += byte
            # Prevent buffer overflow
            if len(uart_buffer) > 256:
                uart_buffer = b""
                send_uart_response("error:buffer_overflow")
    
    # Check for USB/stdin commands
    try:
        result = select.select([sys.stdin], [], [], 0)
        if result and result[0]:
            line = sys.stdin.readline()
            if line:
                process_command(line.strip(), source="usb")
    except:
        pass
    
    utime.sleep_ms(100)
