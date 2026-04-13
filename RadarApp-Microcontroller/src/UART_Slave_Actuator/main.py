# MicroPython UART Slave - Servo Actuator Controller
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
# UART Slave (on shared UART1 bus with device addressing)
# Command Format: servo:COMMAND[:ARGS]
# Response Format: servo:status[:DATA]
# Commands: ping, status, whoami, open, close

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
# UART1: Slave communication bus (shared with stepper and radar)
uart_slaves = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
print("[STARTUP] UART slave initialized (TX=GPIO4, RX=GPIO5)")

# ============ DEVICE IDENTIFICATION ============
device_name = "servo"

# ============================================================
# servo CONFIGURATION
# ============================================================
# Initialize servo motor PWM on GPIO 2
try:
    servo = PWM(Pin(2))
    servo.freq(50)  # 50Hz for RC servo
    servo.duty_u16(3276)  # Start in closeD position (~1ms pulse)
    print("[INIT] Servo PWM initialized on GPIO 2 (closed position)")
except Exception as e:
    print(f"[error] Servo init failed: {e}")
    servo = None


print("[readY] Waiting for commands on shared UART1 bus")
print("=" * 50 + "\n")

# Track servo state
servo_state = "closeD"  # Start in closeD position
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
    Format: servo:OK:key=val:key=val\n
    
    Args:
        status_msg: Status message (e.g., "OK:state=open" or "error:invalid_command")
    """
    response = f"{device_name}:{status_msg}\n"
    uart_slaves.write(response.encode())
    print(f"[UART-SEND] {response.strip()}")
    return response

def process_uart_command(cmd_text):
    """Process UART command received from master.
    Format: servo:command[:args]
    Response: servo:status[:data]
    
    Supports commands: ping, status, whoami, open, close
    """
    global servo_state
    
    try:
        if not cmd_text:
            send_uart_response("error:empty_command")
            return
        
        # Parse command format: servo:command[:args]
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
            commands = "ping,whoami,status,open,close"
            send_uart_response(f"ok:commands={commands}")
        
        elif cmd == "ping":
            uptime_ms = utime.ticks_ms() - startup_time
            uptime_s = uptime_ms // 1000
            send_uart_response(f"ok:msg=alive:uptime={uptime_s}s")
        
        elif cmd == "whoami":
            send_uart_response(f"ok:device=servo:type=actuator")
        
        elif cmd == "status":
            send_uart_response(f"ok:state={servo_state.lower()}:device=servo")
        
        # ========== CONTROL COMMANDS ==========
        elif cmd == "open":
            print("[servo] Moving to open position")
            if servo:
                servo.duty_u16(6553)  # ~2ms pulse (full extension)
            servo_state = "open"
            print(f"[servo] Waiting 6 seconds for movement to complete...")
            utime.sleep_ms(6000)  # Wait for servo to complete movement
            send_uart_response(f"ok:msg=opened:state=open")
        
        elif cmd == "close":
            print("[servo] Moving to close position")
            if servo:
                servo.duty_u16(3276)  # ~1ms pulse (full retraction)
            servo_state = "closed"
            print(f"[servo] Waiting 6 seconds for movement to complete...")
            utime.sleep_ms(6000)  # Wait for servo to complete movement
            send_uart_response(f"ok:msg=closed:state=closed")
        
        else:
            send_uart_response(f"error:unknown_command:{cmd}")
    
    except Exception as e:
        print(f"[UART-ERR] Command processing error: {type(e).__name__}: {e}")
        send_uart_response(f"error:command_error:{str(e)[:30]}")

print("=" * 50)
print("Servo Actuator Pico Firmware - UART REST API Compatible")
print("=" * 50)
print(f"[readY] UART Slave ({device_name}) initialized")
print("[servo] Servo control via PWM on GPIO 2")
print(f"[WIRING] PWM on GPIO 2, UART on UART1 (shared bus)")
print()
print("UART Protocol (shared bus with stepper and radar):")
print("  Format: servo:COMMAND[:ARGS]")
print("  Response: servo:status[:DATA]")
print()
print("Available Commands:")
print("  ping           - Alive check")
print("  status         - Get servo status (current state)")
print("  whoami         - Device identification")
print("  open           - Extend/open servo actuator")
print("  close          - Retract/close servo actuator")
print()
print("Examples:")
print("  servo:ping")
print("  servo:status")
print("  servo:open")
print("  servo:close")
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
                send_uart_response("error:buffer_overflow")
    
    utime.sleep_ms(10)
