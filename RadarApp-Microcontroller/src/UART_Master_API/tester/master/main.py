# UART Master - Servo Control Tester
# Sends commands to servo slave and reads responses

# Disable WiFi/Bluetooth to avoid CYW43 interference
try:
    import network
    network.country('US')  # Set country first
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    print("[OK] WiFi disabled")
except Exception as e:
    print(f"[WARN] WiFi disable failed: {e}")

from machine import UART, Pin
import utime

print("=" * 60)
print("UART MASTER - Servo Control Tester")
print("=" * 60)

# LED for activity indication
led = Pin("LED", Pin.OUT)
led.on()
print("[INIT] LED turned ON")

# Initialize UART0 (TX=Pin(0), RX=Pin(1), 115200 baud)
uart = None
try:
    uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
    print("[INIT] UART initialized on UART0")
except Exception as e:
    print(f"[ERROR] UART init failed: {e}")

if uart:
    print("[READY] Connected to shared UART bus\n")
    
    # Device addresses on the bus
    DEVICES = {
        "SERVO": {"timeout": 8000},    # OPEN/CLOSE take 6s
        "STEPPER": {"timeout": 5000},  # Adjust as needed
        "RADAR": {"timeout": 2000},    # Quick reads
    }
    
    def flush_uart_buffer():
        """Clear any stale data in UART buffer"""
        while uart.any():
            uart.read()
        utime.sleep_ms(50)
    
    def send_command(device, cmd):
        """Send a device-addressed command to the shared UART bus"""
        cmd_with_device = f"{device}:{cmd}"
        cmd_with_newline = cmd_with_device + "\n" if not cmd_with_device.endswith("\n") else cmd_with_device
        print(f"\n[SEND] {cmd_with_device}")
        
        # Flash LED to indicate transmission
        led.off()
        utime.sleep_ms(50)
        uart.write(cmd_with_newline.encode())
        utime.sleep_ms(50)
        led.on()
    
    def read_response(timeout_ms=2000):
        """Read response from servo until newline or timeout"""
        response = b""
        start_time = utime.ticks_ms()
        
        while (utime.ticks_ms() - start_time) < timeout_ms:
            if uart.any():
                byte = uart.read(1)
                if byte == b'\n':
                    # End of response
                    if response:
                        return response
                    # Skip empty lines
                else:
                    response += byte
            else:
                utime.sleep_ms(5)
        
        return response if response else None
    
    def send_and_wait(device, cmd, timeout_ms=None, retries=2):
        """Send device-addressed command and wait for response with retry logic"""
        # Use device-specific timeout if not provided
        if timeout_ms is None:
            timeout_ms = DEVICES.get(device, {}).get("timeout", 2000)
        
        is_ping = (cmd.upper() == "PING")
        is_action = (cmd.upper() in ["OPEN", "CLOSE"])
        
        # Override timeout for long-running actions
        if is_action and device == "SERVO":
            timeout_ms = 8000
        
        send_time = None
        
        for attempt in range(1, retries + 1):
            try:
                # Clear buffer before sending
                flush_uart_buffer()
                utime.sleep_ms(100)
                
                # Record send time for PING commands
                if is_ping:
                    send_time = utime.ticks_ms()
                
                # Send device-addressed command
                send_command(device, cmd)
                
                # Wait for response
                print(f"  Waiting for response (timeout: {timeout_ms}ms)...")
                response = read_response(timeout_ms=timeout_ms)
                
                if response:
                    resp_text = response.decode().strip()
                    
                    # Verify response is from correct device
                    if resp_text.startswith(device + ":"):
                        # Calculate round-trip time for PING
                        if is_ping and send_time is not None:
                            rtt_ms = utime.ticks_ms() - send_time
                            print(f"  [RECV] {resp_text} (RTT: {rtt_ms}ms)")
                        else:
                            print(f"  [RECV] {resp_text}")
                        return resp_text
                    else:
                        print(f"  [WRONG DEVICE] Expected {device}, got: {resp_text}")
                        # Don't retry, move on
                        return None
                else:
                    print(f"  [TIMEOUT] No response received")
                    if attempt < retries:
                        print(f"  Retry {attempt}/{retries - 1}...")
                        utime.sleep(0.5)
                    
            except Exception as e:
                print(f"  [ERROR] {e}")
                if attempt < retries:
                    print(f"  Retry {attempt}/{retries - 1}...")
                    utime.sleep(0.5)
        
        return None
    
    # Test sequence
    print("=" * 60)
    print("SERVO TEST SEQUENCE")
    print("=" * 60)
    
    # First, test PING
    print("\n[TEST] Sending PING to SERVO to verify connection...")
    response = send_and_wait("SERVO", "PING", timeout_ms=2000, retries=2)
    if response and "OK" in response:
        print("[SUCCESS] SERVO is responding!\n")
    else:
        print("[FAILED] No response from SERVO\n")
    
    # Main control loop
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            
            # Open
            print(f"\n[CYCLE {cycle_count}] Commanding SERVO to OPEN...")
            send_and_wait("SERVO", "OPEN", timeout_ms=8000, retries=2)
            utime.sleep(1)
            
            # Close
            print(f"\n[CYCLE {cycle_count}] Commanding SERVO to CLOSE...")
            send_and_wait("SERVO", "CLOSE", timeout_ms=8000, retries=2)
            utime.sleep(1)
            
            # Ping (to verify still connected)
            print(f"\n[CYCLE {cycle_count}] Checking SERVO connection with PING...")
            response = send_and_wait("SERVO", "PING", timeout_ms=2000, retries=1)
            
            if not response:
                print("[WARNING] Lost connection to SERVO! Restarting cycle...")
            
            utime.sleep(1)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print(f"STOPPED after {cycle_count} cycles")
        print("=" * 60)
        led.off()
        utime.sleep_ms(100)
        led.on()
else:
    print("[ERROR] Could not initialize UART")
