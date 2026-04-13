#!/usr/bin/env python3
"""
Raspberry Pi UART Command Sender
Sends commands to Pico Master and displays responses
Run with: python3 test_pi_sender.py
"""

import serial
import time
import sys

def main():
    PORT = '/dev/ttyAMA0'
    BAUD = 460800
    
    try:
        print("=" * 70)
        print("Raspberry Pi UART Command Sender")
        print("=" * 70)
        print(f"Port: {PORT}")
        print(f"Baud: {BAUD}")
        print("\nCommands:")
        print("  servo:ping")
        print("  servo:status")
        print("  stepper:ping")
        print("  stepper:status")
        print("  RADAR:ping")
        print("  HELP")
        print("\nType 'quit' or 'exit' to stop\n")
        
        ser = serial.Serial(PORT, BAUD, timeout=2)
        time.sleep(0.5)  # Wait for Pico to be ready
        
        while True:
            try:
                # Get command from user
                cmd = input("→ Send: ").strip()
                
                if not cmd:
                    continue
                
                if cmd.lower() in ['quit', 'exit']:
                    print("Exiting...")
                    break
                
                # Send command with newline
                print(f"  Sending: {cmd}")
                ser.write(f"{cmd}\n".encode())
                
                # Read response
                time.sleep(0.5)
                if ser.in_waiting:
                    response = ser.readline().decode('utf-8', errors='replace').strip()
                    print(f"← Received: {response}\n")
                else:
                    print("← No response\n")
                    
            except KeyboardInterrupt:
                print("\nInterrupted")
                break
            except Exception as e:
                print(f"Error: {e}\n")
        
        ser.close()
        print("✓ Closed")
        
    except serial.SerialException as e:
        print(f"✗ Serial Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
