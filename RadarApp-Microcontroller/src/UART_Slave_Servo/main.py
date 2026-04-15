# v.Final J. 2026-04-13
# Servo servo controller code for Raspberry Pi Pico using MicroPython
# # MicroPython UART Slave - Servo Servo Controller
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
# UART Slave (on shared UART1 bus with device addressing)
# Command Format: servo:command[:args]
# Response Format: servo:status[:data]
# Commands: ping, status, whoami, open, close

from machine import UART, Pin, PWM
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
device_name = "servo"

# ============ SUPPORTED COMMANDS ============
SUPPORTED_COMMANDS = ["commands", "ping", "whoami", "status", "open", "close"]

# ============================================================
# servo CONFIGURATION
# ============================================================
# Initialize servo motor PWM on GPIO 2
try:
    servo = PWM(Pin(2))
    servo.freq(50)  # 50Hz for RC servo
    servo.duty_u16(3276)  # Start in closed position (~1ms pulse)
    print("[INIT] Servo PWM initialized on GPIO 2 (closed position)")
except Exception as e:
    print(f"[error] Servo init failed: {e}")
    servo = None


print("[readY] Waiting for commands on shared UART1 bus")
print("=" * 50 + "\n")

# Track servo state
servo_state = "closed"  # Start in closed position
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
    Format: servo:ok:key=val:key=val\n
    
    Args:
        status_msg: Status message (e.g., "ok:state=open" or "error:invalid_command")
    """
    # Small delay to let master clear its RX buffer after command transmission
    utime.sleep_ms(50)
    
    response = f"{device_name}:{status_msg}\n"
    uart_slaves.write(response.encode())
    utime.sleep_ms(10)  # Allow buffer to flush on shared UART bus
    print(f"[UART-SEND] {response.strip()}")
    return response

def process_uart_command(cmd_text):
    """Deprecated - now routed to unified process_command"""
    process_command(cmd_text, source="uart")

def simple_response(cmd, status, **kwargs):
    """Create simple text response - colon-separated format"""
    parts = [status]
    for k, v in kwargs.items():
        parts.append(f"{k}={v}")
    return ":".join(parts)

def process_command(cmd_text, source="unknown"):
    """Process command from either UART or USB/REPL.
    Format: servo:command[:args]
    Sends response via send_uart_response
    """
    global servo_state
    try:
        if not cmd_text:
            if source == "usb":
                send_uart_response("error:empty_command")
            return
        cmd_text = cmd_text.strip().lower()
        
        print(f"[CMD-{source.lower()}] {cmd_text}")
        
        # Parse command format: servo:command[:args]
        parts = cmd_text.split(":", 2)
        
        if len(parts) < 2:
            # Handle legacy format: just "ping" -> auto-prefix with device
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
            uptime_ms = utime.ticks_ms() - startup_time
            uptime_s = uptime_ms // 1000
            send_uart_response(f"ok:msg=alive:uptime={uptime_s}s")
        
        elif cmd == "whoami":
            send_uart_response(f"ok:device=servo:type=servo")
        
        elif cmd == "status":
            send_uart_response(f"ok:state={servo_state.lower()}:device=servo")
        
        # ========== CONTROL COMMANDS ========== 
        elif cmd == "open":
            print("[servo] Moving to open position")
            if servo:
                servo.duty_u16(6553)  # ~2ms pulse (full extension)
                servo_state = "open"
                send_uart_response(f"ok:msg=opened:state=open")
            else:
                send_uart_response(f"error:servo_not_initialized")
        
        elif cmd == "close":
            print("[servo] Moving to close position")
            if servo:
                servo.duty_u16(3276)  # ~1ms pulse (full retraction)
                servo_state = "closed"
                send_uart_response(f"ok:msg=closed:state=closed")
            else:
                send_uart_response(f"error:servo_not_initialized")
        
        else:
            send_uart_response(f"error:unknown_command:{cmd}")
    
    except Exception as e:
        print(f"[CMD-ERR] Processing error: {type(e).__name__}: {e}")
        send_uart_response(f"error:command_error:{str(e)[:30]}")

print("=" * 50)
print("Servo Servo Pico Firmware - UART REST API Compatible")
print("=" * 50)
print(f"[readY] UART Slave ({device_name}) initialized")
print("[servo] Servo control via PWM on GPIO 2")
print(f"[WIRING] PWM on GPIO 2, UART on UART1 (shared bus)")
print()
print("UART Protocol (shared bus with stepper and radar):")
print("  Format: servo:command[:args]")
print("  Response: servo:status[:DATA]")
print()
print("Available Commands:")
print("  ping           - Alive check")
print("  status         - Get servo status (current state)")
print("  whoami         - Device identification")
print("  open           - Extend/open servo servo")
print("  close          - Retract/close servo servo")
print()
print("Examples:")
print("  servo:ping")
print("  servo:status")
print("  servo:open")
print("  servo:close")
print("=" * 50)
print()

# Main loop
uart_buffer = b""  # Buffer for reading UART data
last_blink_time = utime.ticks_ms()
led_state = True
blink_interval = 500  # 500ms on/off for visibility

print("[INIT] Starting main loop...")
print()

while True:
    # Accurate LED blinking (500ms on, 500ms off)
    current_time = utime.ticks_ms()
    if current_time - last_blink_time >= blink_interval:
        last_blink_time = current_time
        led_state = not led_state
        if led_state:
            led.on()
        else:
            led.off()
    
    # Check for incoming UART data (commands from master)
    while uart_slaves.any():
        byte = uart_slaves.read(1)
        if byte == b'\n':
            # Complete command received
            cmd_text = uart_buffer.decode().strip()
            uart_buffer = b""
            
            if cmd_text:
                print(f"[UART-RECV] {cmd_text}")
                process_command(cmd_text, source="uart")
        elif byte:
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
    
    utime.sleep_ms(10)
