# Raw UART Data Tester
# MicroPython test script for Raspberry Pi Pico
# Captures and displays raw UART data for debugging
# Shows hex, ASCII, and parsed formats

from machine import UART, Pin
import utime

print("=" * 70)
print("RAW UART DATA TESTER")
print("Real-time UART bus monitoring and debugging")
print("=" * 70)
print()

# ============================================================
# UART CONFIGURATION
# ============================================================
# Matches main.py UART setup for Pico Master

UART_PORT = 1               # UART1
TX_PIN = 4                  # GPIO 4 (TX)
RX_PIN = 5                  # GPIO 5 (RX)
BAUD_RATE = 115200

uart = UART(UART_PORT, baudrate=BAUD_RATE, tx=Pin(TX_PIN), rx=Pin(RX_PIN))

print(f"UART Configuration:")
print(f"  Port:       UART{UART_PORT}")
print(f"  TX Pin:     GPIO{TX_PIN}")
print(f"  RX Pin:     GPIO{RX_PIN}")
print(f"  Baud Rate:  {BAUD_RATE}")
print()

led = Pin("LED", Pin.OUT)
led.on()

# ============================================================
# RAW DATA PARSER
# ============================================================

class RawUARTMonitor:
    """Monitor and parse raw UART data"""
    
    def __init__(self, uart):
        self.uart = uart
        self.buffer = b''
        self.timeout_ms = 1000
        self.stats = {
            'bytes_rx': 0,
            'bytes_tx': 0,
            'messages': 0,
            'errors': 0
        }
    
    def read_raw_bytes(self, count=100):
        """Read raw bytes from UART
        
        Args:
            count: Max bytes to read
            
        Returns:
            bytes object
        """
        data = self.uart.read(count)
        if data:
            self.stats['bytes_rx'] += len(data)
            self.buffer += data
        return data
    
    def wait_for_data(self, timeout_ms=1000):
        """Wait for data with timeout
        
        Returns:
            bytes if data available, None if timeout
        """
        start = utime.ticks_ms()
        
        while utime.ticks_diff(utime.ticks_ms(), start) < timeout_ms:
            if self.uart.any():
                return self.read_raw_bytes()
            utime.sleep_ms(10)
        
        return None
    
    def send_raw(self, data):
        """Send raw bytes
        
        Args:
            data: bytes or string to send
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        self.uart.write(data)
        self.stats['bytes_tx'] += len(data)
    
    def format_hex(self, data, width=16):
        """Format data as hex dump
        
        Args:
            data: bytes to format
            width: bytes per line
            
        Returns:
            formatted string
        """
        lines = []
        for i in range(0, len(data), width):
            chunk = data[i:i+width]
            hex_part = ' '.join('{:02x}'.format(b) for b in chunk)
            ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            lines.append(f"  {i:04x}: {hex_part:<{width*3-1}}  {ascii_part}")
        
        return '\n'.join(lines) if lines else "  (empty)"
    
    def format_line(self, data):
        """Format as single line (raw and hex)
        
        Returns:
            formatted string
        """
        hex_str = ' '.join('{:02x}'.format(b) for b in data)
        
        try:
            ascii_str = data.decode('utf-8', errors='replace')
        except:
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
        
        return f"Hex: {hex_str}\nASCII: {repr(ascii_str)}"
    
    def split_messages(self, delimiter=b'\n'):
        """Split buffer into messages (defaults to newline delimiter)
        
        Args:
            delimiter: message delimiter (default: newline)
            
        Returns:
            list of complete messages, remainder in buffer
        """
        messages = []
        
        while delimiter in self.buffer:
            idx = self.buffer.index(delimiter)
            msg = self.buffer[:idx]
            self.buffer = self.buffer[idx+len(delimiter):]
            messages.append(msg)
        
        return messages
    
    def get_stats(self):
        """Get statistics"""
        return self.stats.copy()

monitor = RawUARTMonitor(uart)

print("Monitor initialized. Listening for UART data...")
print()

# ============================================================
# TEST FUNCTIONS
# ============================================================

def show_menu():
    """Display test menu"""
    print("\nRAW DATA TESTER MENU")
    print("-" * 70)
    print("1. Continuous Hex Monitor    - Live hex display (Ctrl+C to stop)")
    print("2. Line-by-Line Monitor      - Show complete messages")
    print("3. Single Capture            - Capture one message")
    print("4. Timed Capture             - Capture for N seconds")
    print("5. Send Raw Command          - Send custom UART data")
    print("6. Stats & Buffer Info       - Show statistics")
    print("7. Raw Hex Dump              - Display buffer as hex dump")
    print("8. Clear Buffer              - Clear receive buffer")
    print("9. Test Devices              - Send PING to all devices")
    print("A. Exit                      - Exit test")
    print("-" * 70)

def continuous_hex_monitor():
    """Continuous monitoring with hex display"""
    print("CONTINUOUS HEX MONITOR (Ctrl+C to stop)")
    print("-" * 70)
    
    captured = b''
    
    try:
        while True:
            data = monitor.read_raw_bytes(32)
            
            if data:
                captured += data
                
                # Display in real-time
                print(f"[{utime.time():.2f}] RX {len(data)} bytes:")
                print(monitor.format_hex(data, width=16))
                print()
            
            utime.sleep_ms(100)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    
    if captured:
        print("\nTotal captured:")
        print(monitor.format_hex(captured, width=16))

def line_by_line_monitor():
    """Monitor line-by-line (newline delimited)"""
    print("LINE-BY-LINE MONITOR (Ctrl+C to stop)")
    print("Waiting for newline-delimited messages...")
    print("-" * 70)
    
    msg_count = 0
    
    try:
        while True:
            data = monitor.read_raw_bytes(64)
            
            if data:
                # Check for complete messages
                messages = monitor.split_messages(b'\n')
                
                for msg in messages:
                    msg_count += 1
                    timestamp = utime.time()
                    
                    print(f"\n[{timestamp:.2f}] Message {msg_count}:")
                    print(f"  Raw bytes: {len(msg)}")
                    print(f"  Hex:   {' '.join('{:02x}'.format(b) for b in msg)}")
                    
                    try:
                        decoded = msg.decode('utf-8')
                        print(f"  ASCII: {repr(decoded)}")
                    except:
                        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in msg)
                        print(f"  ASCII: {ascii_str}")
                    
                    print(f"  Remaining buffer: {len(monitor.buffer)} bytes")
            
            utime.sleep_ms(50)
    
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped")
        print(f"Captured {msg_count} complete messages")

def single_capture():
    """Capture one message"""
    print("SINGLE CAPTURE - Waiting for data...")
    print("-" * 70)
    
    data = monitor.wait_for_data(5000)  # 5 second timeout
    
    if data:
        print(f"\nCaptured {len(data)} bytes:")
        print("\nHex Dump:")
        print(monitor.format_hex(data))
        print()
        print(monitor.format_line(data))
    else:
        print("\nTimeout: No data received")

def timed_capture():
    """Capture for specified duration"""
    print("TIMED CAPTURE")
    
    try:
        duration = int(input("Capture duration (seconds) [10]: ") or "10")
    except:
        duration = 10
    
    print(f"\nCapturing for {duration} seconds...")
    print("-" * 70)
    
    start = utime.time()
    captured = b''
    
    try:
        while utime.time() - start < duration:
            data = monitor.read_raw_bytes(64)
            if data:
                captured += data
                elapsed = utime.time() - start
                print(f"[{elapsed:.1f}s] RX {len(data)} bytes (total: {len(captured)})")
            
            utime.sleep_ms(50)
    
    except KeyboardInterrupt:
        print("\nCapture interrupted")
    
    elapsed = utime.time() - start
    
    print("\n" + "-" * 70)
    print(f"Capture complete: {len(captured)} bytes in {elapsed:.1f} seconds")
    print()
    print("Hex Dump:")
    print(monitor.format_hex(captured))

def send_raw_command():
    """Send custom UART data"""
    print("SEND RAW COMMAND")
    print("-" * 70)
    print("Formats:")
    print("  Text:  RADAR:PING\\n")
    print("  Hex:   48 65 6C 6C 6F (space-separated hex bytes)")
    print()
    
    cmd = input("Enter command/data: ")
    
    if not cmd:
        print("Empty command")
        return
    
    # Try to parse as hex if it looks like hex
    if all(c in '0123456789abcdefABCDEF ' for c in cmd):
        try:
            hex_bytes = bytes.fromhex(cmd)
            print(f"\nSending {len(hex_bytes)} bytes (parsed as hex):")
            print(f"  {' '.join('{:02x}'.format(b) for b in hex_bytes)}")
            monitor.send_raw(hex_bytes)
        except:
            # Not valid hex, send as text
            print(f"\nSending as text:")
            print(f"  {repr(cmd)}")
            monitor.send_raw(cmd)
    else:
        # Send as text
        print(f"\nSending as text:")
        print(f"  {repr(cmd)}")
        monitor.send_raw(cmd)
    
    print("✓ Sent")

def show_stats():
    """Show statistics"""
    stats = monitor.get_stats()
    
    print("\nSTATISTICS & BUFFER INFO")
    print("-" * 70)
    print(f"RX Bytes:        {stats['bytes_rx']}")
    print(f"TX Bytes:        {stats['bytes_tx']}")
    print(f"Messages:        {stats['messages']}")
    print(f"Errors:          {stats['errors']}")
    print(f"Buffer size:     {len(monitor.buffer)} bytes")
    print()
    
    if monitor.buffer:
        print(f"Buffer content (first 64 bytes):")
        preview = monitor.buffer[:64]
        print(f"  Hex: {' '.join('{:02x}'.format(b) for b in preview)}")
        try:
            ascii_str = preview.decode('utf-8', errors='replace')
            print(f"  ASCII: {repr(ascii_str)}")
        except:
            pass

def show_hex_dump():
    """Show buffer as hex dump"""
    print("\nRAW HEX DUMP - Buffer Contents")
    print("-" * 70)
    
    if not monitor.buffer:
        print("Buffer is empty")
        return
    
    print(f"Total: {len(monitor.buffer)} bytes\n")
    print(monitor.format_hex(monitor.buffer))

def clear_buffer():
    """Clear the buffer"""
    print("\nClear buffer?")
    size = len(monitor.buffer)
    
    if size > 0:
        confirm = input(f"Clear {size} bytes? (y/n): ")
        if confirm.lower() == 'y':
            monitor.buffer = b''
            print("✓ Buffer cleared")
        else:
            print("✗ Cancelled")
    else:
        print("Buffer already empty")

def test_devices():
    """Send PING to all devices"""
    print("\nTEST DEVICES - Sending PINGs")
    print("-" * 70)
    
    devices = [
        ('STEPPER', 0x10),
        ('SERVO', 0x11),
        ('RADAR', 0x20)
    ]
    
    for name, addr in devices:
        cmd = f"{name}:PING\n"
        print(f"Sending: {name}:PING (addr 0x{addr:02x})")
        monitor.send_raw(cmd)
        utime.sleep_ms(100)
    
    print("\nWaiting for responses (5 seconds)...")
    print("-" * 70)
    
    start = utime.time()
    responses = []
    
    try:
        while utime.time() - start < 5:
            data = monitor.read_raw_bytes(64)
            if data:
                responses.append(data)
                # Try to parse message
                try:
                    decoded = data.decode('utf-8')
                    print(f"Response: {repr(decoded)}")
                except:
                    print(f"Response (hex): {' '.join('{:02x}'.format(b) for b in data)}")
            
            utime.sleep_ms(50)
    
    except KeyboardInterrupt:
        pass
    
    print(f"\nReceived {len(b''.join(responses))} bytes total")

# ============================================================
# MAIN LOOP
# ============================================================

try:
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect option (1-A): ").strip().upper()
            
            if choice == "1":
                continuous_hex_monitor()
            elif choice == "2":
                line_by_line_monitor()
            elif choice == "3":
                single_capture()
            elif choice == "4":
                timed_capture()
            elif choice == "5":
                send_raw_command()
            elif choice == "6":
                show_stats()
            elif choice == "7":
                show_hex_dump()
            elif choice == "8":
                clear_buffer()
            elif choice == "9":
                test_devices()
            elif choice == "A":
                print("\nExiting...")
                break
            else:
                print("Invalid choice. Please select 1-A.")
        
        except KeyboardInterrupt:
            print("\n(Returning to menu)")
        except Exception as e:
            print(f"Error: {e}")

except KeyboardInterrupt:
    print("\n\nTest terminated by user")

finally:
    led.off()
    print("Raw data tester complete!")
