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
print("UART master - Servo Control Tester")
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
    print(f"[error] UART init failed: {e}")

if uart:
    print("[readY] Connected to shared UART bus\n")
    
    # Device addresses on the bus
    DEVICES = {
        "servo": {"timeout": 8000},    # open/close take 6s
        "stepper": {"timeout": 5000},  # Adjust as needed
        "radar": {"timeout": 2000},    # Quick reads
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
        
        is_ping = (cmd.lower() == "ping")
        is_action = (cmd.lower() in ["open", "close"])
        
        # Override timeout for long-running actions
        if is_action and device == "servo":
            timeout_ms = 8000
        
        send_time = None
        
        for attempt in range(1, retries + 1):
            try:
                # Clear buffer before sending
                flush_uart_buffer()
                utime.sleep_ms(100)
                
                # Record send time for ping commands
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
                        # Calculate round-trip time for ping
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
                print(f"  [error] {e}")
                if attempt < retries:
                    print(f"  Retry {attempt}/{retries - 1}...")
                    utime.sleep(0.5)
        
        return None
    
    # Test sequence
    print("=" * 60)
    print("servo TEST SEQUENCE")
    print("=" * 60)
    
    # First, test ping
    print("\n[TEST] Sending ping to servo to verify connection...")
    response = send_and_wait("servo", "ping", timeout_ms=2000, retries=2)
    if response and "OK" in response:
        print("[SUCCESS] servo is responding!\n")
    else:
        print("[FAILED] No response from servo\n")
    
    # Main control loop
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            
            # Open
            print(f"\n[CYCLE {cycle_count}] Commanding servo to open...")
            send_and_wait("servo", "open", timeout_ms=8000, retries=2)
            utime.sleep(1)
            
            # Close
            print(f"\n[CYCLE {cycle_count}] Commanding servo to close...")
            send_and_wait("servo", "close", timeout_ms=8000, retries=2)
            utime.sleep(1)
            
            # Ping (to verify still connected)
            print(f"\n[CYCLE {cycle_count}] Checking servo connection with ping...")
            response = send_and_wait("servo", "ping", timeout_ms=2000, retries=1)
            
            if not response:
                print("[WARNING] Lost connection to servo! Restarting cycle...")
            
            utime.sleep(1)
            
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print(f"stopPED after {cycle_count} cycles")
        print("=" * 60)
        led.off()
        utime.sleep_ms(100)
        led.on()
else:
    print("[error] Could not initialize UART")
