# MicroPython UART Slave - Servo Actuator Controller
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
# UART Slave (on shared UART1 bus with device addressing)
# Command Format: SERVO:COMMAND[:ARGS]
# Response Format: SERVO:STATUS[:DATA]
# Commands: PING, STATUS, WHOAMI, OPEN, CLOSE

from machine import UART, Pin, PWM
import utime
import sys

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
# UART1: Slave communication bus (shared with STEPPER and RADAR)
uart_slaves = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
print("[STARTUP] UART slave initialized (TX=GPIO4, RX=GPIO5)")

# ============ DEVICE IDENTIFICATION ============
DEVICE_NAME = "SERVO"

# ============================================================
# SERVO CONFIGURATION
# ============================================================
# Initialize servo motor PWM on GPIO 2
try:
    servo = PWM(Pin(2))
    servo.freq(50)  # 50Hz for RC servo
    servo.duty_u16(3276)  # Start in CLOSED position (~1ms pulse)
    print("[INIT] Servo PWM initialized on GPIO 2 (closed position)")
except Exception as e:
    print(f"[ERROR] Servo init failed: {e}")
    servo = None


print("[READY] Waiting for commands on shared UART1 bus")
print("=" * 50 + "\n")

# Track servo state
servo_state = "CLOSED"  # Start in CLOSED position
startup_time = utime.ticks_ms()  # Record startup time for uptime tracking

# ============ UART COMMUNICATION LAYER ============

def flush_uart_buffer():
    """Clear any stale data in UART buffer"""
    while uart_slaves.any():
        uart_slaves.read()
    utime.sleep_ms(50)

def send_uart_response(status_msg):
    """
    Send device-addressed response via UART.
    Format: SERVO:OK:key=val:key=val\n
    
    Args:
        status_msg: Status message (e.g., "OK:state=open" or "ERROR:invalid_command")
    """
    response = f"{DEVICE_NAME}:{status_msg}\n"
    uart_slaves.write(response.encode())
    print(f"[UART-SEND] {response.strip()}")
    return response

def process_uart_command(cmd_text):
    """Process UART command received from master.
    Format: SERVO:COMMAND[:ARGS]
    Response: SERVO:STATUS[:DATA]
    
    Supports commands: PING, STATUS, WHOAMI, OPEN, CLOSE
    """
    global servo_state
    
    try:
        if not cmd_text:
            send_uart_response("ERROR:empty_command")
            return
        
        # Parse command format: SERVO:COMMAND[:ARGS]
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
            uptime_ms = utime.ticks_ms() - startup_time
            uptime_s = uptime_ms // 1000
            send_uart_response(f"OK:msg=alive:uptime={uptime_s}s")
        
        elif cmd == "WHOAMI":
            send_uart_response(f"OK:device=SERVO:type=actuator")
        
        elif cmd == "STATUS":
            send_uart_response(f"OK:state={servo_state.lower()}:device=servo")
        
        # ========== CONTROL COMMANDS ==========
        elif cmd == "OPEN":
            print("[SERVO] Moving to OPEN position")
            if servo:
                servo.duty_u16(6553)  # ~2ms pulse (full extension)
            servo_state = "OPEN"
            print(f"[SERVO] Waiting 6 seconds for movement to complete...")
            utime.sleep_ms(6000)  # Wait for servo to complete movement
            send_uart_response(f"OK:msg=opened:state=open")
        
        elif cmd == "CLOSE":
            print("[SERVO] Moving to CLOSE position")
            if servo:
                servo.duty_u16(3276)  # ~1ms pulse (full retraction)
            servo_state = "CLOSED"
            print(f"[SERVO] Waiting 6 seconds for movement to complete...")
            utime.sleep_ms(6000)  # Wait for servo to complete movement
            send_uart_response(f"OK:msg=closed:state=closed")
        
        else:
            send_uart_response(f"ERROR:unknown_command:{cmd}")
    
    except Exception as e:
        print(f"[UART-ERR] Command processing error: {type(e).__name__}: {e}")
        send_uart_response(f"ERROR:command_error:{str(e)[:30]}")

print("=" * 50)
print("Servo Actuator Pico Firmware - UART REST API Compatible")
print("=" * 50)
print(f"[READY] UART Slave ({DEVICE_NAME}) initialized")
print("[SERVO] Servo control via PWM on GPIO 2")
print(f"[WIRING] PWM on GPIO 2, UART on UART1 (shared bus)")
print()
print("UART Protocol (shared bus with STEPPER and RADAR):")
print("  Format: SERVO:COMMAND[:ARGS]")
print("  Response: SERVO:STATUS[:DATA]")
print()
print("Available Commands:")
print("  PING           - Alive check")
print("  STATUS         - Get servo status (current state)")
print("  WHOAMI         - Device identification")
print("  OPEN           - Extend/open servo actuator")
print("  CLOSE          - Retract/close servo actuator")
print()
print("Examples:")
print("  SERVO:PING")
print("  SERVO:STATUS")
print("  SERVO:OPEN")
print("  SERVO:CLOSE")
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
    
    utime.sleep_ms(10)
