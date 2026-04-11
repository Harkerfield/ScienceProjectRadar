# UART Slave - Servo Control via UART Commands
# Receives commands and sends responses back
from machine import UART, Pin, PWM
import utime

# Disable WiFi/Bluetooth to avoid CYW43 interference
try:
    import network
    network.country('US')  # Set country first
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    print("[OK] WiFi disabled")
except Exception as e:
    print(f"[WARN] WiFi disable failed: {e}")

print("=" * 60)
print("UART SERVO SLAVE - Waiting for commands")
print("=" * 60)

# LED for activity indication
led = Pin("LED", Pin.OUT)
led.on()
print("[INIT] LED turned ON")

# Initialize servo motor PWM on GPIO 2
try:
    servo = PWM(Pin(2))
    servo.freq(50)  # 50Hz for RC servo
    servo.duty_u16(3276)  # Start in CLOSED position (~1ms pulse)
    print("[INIT] Servo PWM initialized on GPIO 2 (closed position)")
except Exception as e:
    print(f"[ERROR] Servo init failed: {e}")
    servo = None

# Initialize UART0 (TX=Pin(0), RX=Pin(1), 115200 baud)
try:
    uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
    print("[INIT] UART initialized on UART0")
except Exception as e:
    print(f"[ERROR] UART init failed: {e}")
    uart = None

print("[READY] Waiting for commands: PING, OPEN, CLOSE, WHOAMI, STATUS")
print("=" * 60 + "\n")

# Track servo state
servo_state = "CLOSED"  # Start in CLOSED position
startup_time = utime.ticks_ms()  # Record startup time for uptime tracking

def send_response(response_str):
    """Send response back to master with confirmation"""
    try:
        uart.write(response_str.encode() + b'\n')
        utime.sleep_ms(50)  # Give time for transmission
        print(f"[SEND] {response_str}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send response: {e}")
        return False

def read_command(timeout_ms=500):
    """Read a command from UART until newline or timeout"""
    cmd_data = b""
    start_time = utime.ticks_ms()
    
    while (utime.ticks_ms() - start_time) < timeout_ms:
        if uart.any():
            byte = uart.read(1)
            if byte == b'\n' or byte == b'\r':
                if cmd_data:  # Only return if we have data
                    return cmd_data
            else:
                cmd_data += byte
        utime.sleep_ms(1)
    
    return None if not cmd_data else cmd_data

def process_command(cmd_text):
    """Process servo command and send response"""
    global servo_state
    cmd_text = cmd_text.upper().strip()
    print(f"\n[RECV] Raw command: {cmd_text}")
    
    # Parse device:command format
    if ":" in cmd_text:
        parts = cmd_text.split(":", 1)
        device_id = parts[0]
        command = parts[1] if len(parts) > 1 else ""
    else:
        device_id = "UNKNOWN"
        command = cmd_text
    
    # Check if this command is for us
    if device_id != "SERVO":
        print(f"[IGNORE] Command is for {device_id}, not SERVO")
        return
    
    print(f"[CMD] {command}")
    
    response = None
    action_wait_ms = 0  # Time to wait before sending response
    
    if command == "PING":
        uptime_ms = utime.ticks_ms() - startup_time
        uptime_s = uptime_ms // 1000
        response = f"SERVO:PING:OK:UPTIME={uptime_s}s"
        
    elif command == "OPEN":
        print("[SERVO] Moving to OPEN position")
        if servo:
            servo.duty_u16(6553)  # ~2ms pulse (full extension)
        servo_state = "OPEN"
        response = "SERVO:OPEN:OK"
        action_wait_ms = 6000  # Wait 6 seconds for servo to complete movement
        print(f"[SERVO] Waiting 6 seconds for movement to complete...")
        
    elif command == "CLOSE":
        print("[SERVO] Moving to CLOSE position")
        if servo:
            servo.duty_u16(3276)  # ~1ms pulse (full retraction)
        servo_state = "CLOSED"
        response = "SERVO:CLOSE:OK"
        action_wait_ms = 6000  # Wait 6 seconds for servo to complete movement
        print(f"[SERVO] Waiting 6 seconds for movement to complete...")
    
    elif command == "WHOAMI":
        response = "SERVO:WHOAMI:ACTUATOR"
    
    elif command == "STATUS":
        response = f"SERVO:STATUS:{servo_state}"
        
    else:
        response = f"SERVO:ERROR:UNKNOWN_CMD:{command}"
    
    # Wait for action to complete if needed
    if action_wait_ms > 0:
        utime.sleep_ms(action_wait_ms)
    
    # Send response
    if response:
        send_response(response)
    
    utime.sleep_ms(100)

# Main loop
print("[START] Entering main loop\n")
loop_count = 0

while True:
    loop_count += 1
    
    # Blink LED slowly to show we're alive
    if loop_count % 100 == 0:
        led.off()
    elif loop_count % 50 == 0:
        led.on()
    
    # Check for incoming command
    if uart and uart.any():
        cmd_data = read_command(timeout_ms=500)
        
        if cmd_data:
            try:
                cmd_text = cmd_data.decode()
                process_command(cmd_text)
            except Exception as e:
                print(f"[ERROR] Failed to process command: {e}")
                send_response("ERROR:DECODE_FAILED")
    
    utime.sleep_ms(10)
