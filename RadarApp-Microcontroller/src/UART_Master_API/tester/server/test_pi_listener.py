#!/usr/bin/env python3
"""
Raspberry Pi UART Listener
Continuously listens to /dev/ttyAMA0 and displays received data
Run with: python3 test_pi_listener.py
or: sudo python3 test_pi_listener.py (if permission denied)
"""

import serial
import time
import sys
from datetime import datetime

def main():
    PORT = '/dev/ttyAMA'
    BAUD = 460800
    
    try:
        print("=" * 70)
        print("Raspberry Pi UART Listener")
        print("=" * 70)
        print(f"Port: {PORT}")
        print(f"Baud: {BAUD}")
        print("Listening for data from Pico Master...")
        print("Press Ctrl+C to stop\n")
        
        ser = serial.Serial(PORT, BAUD, timeout=1)
        print(f"✓ Connected to {PORT} at {BAUD} baud\n")
        
        message_count = 0
        
        while True:
            if ser.in_waiting:
                # Read one line
                line = ser.readline().decode('utf-8', errors='replace').strip()
                
                if line:
                    message_count += 1
                    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                    
                    print(f"[{timestamp}] #{message_count:04d} ← {line}")
                    sys.stdout.flush()
            else:
                # Small delay to prevent CPU spinning
                time.sleep(0.01)
                
    except serial.SerialException as e:
        print(f"\n✗ Serial Error: {e}")
        print("\nTroubleshooting:")
        print("  - Is the Pico connected to GPIO14/15?")
        print("  - Is UART enabled? Check: cat /boot/firmware/config.txt | grep uart")
        print("  - Try with sudo: sudo python3 test_pi_listener.py")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print(f"\n\n✓ Stopped. Received {message_count} messages")
        ser.close()
        sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
