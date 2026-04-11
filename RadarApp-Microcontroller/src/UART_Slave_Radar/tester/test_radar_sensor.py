# Radar Sensor Test - Interactive Viewer
# MicroPython test script for Raspberry Pi Pico radar module
# Allows you to see simulated sensor readings and send commands

from machine import UART, Pin
import utime
import sys

print("=" * 60)
print("RADAR SENSOR TEST - Simulated Readings Viewer")
print("=" * 60)
print()

# UART1: Communication with Radar Pico
uart_test = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
utime.sleep_ms(100)

DEVICE_NAME = "RADAR"

def send_command(cmd, args=""):
    """Send command to radar and get response"""
    if args:
        full_cmd = f"{DEVICE_NAME}:{cmd}:{args}\n"
    else:
        full_cmd = f"{DEVICE_NAME}:{cmd}\n"
    
    print(f"\n>>> Sending: {full_cmd.strip()}")
    uart_test.write(full_cmd.encode())
    
    # Wait for response
    utime.sleep_ms(50)
    response = b""
    while uart_test.any():
        response += uart_test.read(1)
    
    if response:
        response_str = response.decode('utf-8', errors='ignore').strip()
        print(f"<<< Response: {response_str}")
        return response_str
    else:
        print("<<< No response received")
        return None

def parse_response(response):
    """Parse RADAR:OK:key=val:key=val format"""
    if not response or not response.startswith("RADAR:"):
        return None
    
    parts = response.split(":")
    if len(parts) < 2:
        return None
    
    status = parts[1]
    data = {}
    
    for i in range(2, len(parts)):
        if "=" in parts[i]:
            key, val = parts[i].split("=", 1)
            data[key] = val
    
    return {"status": status, "data": data}

def display_radar_status(response):
    """Pretty print radar status"""
    parsed = parse_response(response)
    if not parsed:
        print("Could not parse response")
        return
    
    print("\n" + "=" * 60)
    print("RADAR SENSOR STATUS")
    print("=" * 60)
    
    for key, val in parsed["data"].items():
        if key == "range":
            print(f"  Distance:     {val} cm")
        elif key == "velocity":
            print(f"  Velocity:     {val} m/s")
        elif key == "confidence":
            print(f"  Confidence:   {val}%")
        elif key == "movement":
            print(f"  Movement:     {'DETECTED' if val == '1' else 'None'}")
        elif key == "addr":
            print(f"  Address:      {val}")
        elif key == "device":
            print(f"  Device:       {val}")
        elif key == "type":
            print(f"  Type:         {val}")
        elif key == "msg":
            print(f"  Message:      {val}")
        else:
            print(f"  {key}:        {val}")
    
    print("=" * 60)

def run_test_sequence():
    """Run through test commands"""
    
    print("\n[TEST 1] PING - Check if radar is alive")
    response = send_command("PING")
    if response:
        display_radar_status(response)
    
    utime.sleep_ms(500)
    
    print("\n[TEST 2] WHOAMI - Identify device")
    response = send_command("WHOAMI")
    if response:
        display_radar_status(response)
    
    utime.sleep_ms(500)
    
    print("\n[TEST 3] READ - Get current sensor readings")
    response = send_command("READ")
    if response:
        display_radar_status(response)
    
    utime.sleep_ms(500)
    
    print("\n[TEST 4] STATUS - Get detailed status")
    response = send_command("STATUS")
    if response:
        display_radar_status(response)
    
    utime.sleep_ms(500)
    
    print("\n[TEST 5] SET_RANGE - Simulate new distance reading (250cm)")
    response = send_command("SET_RANGE", "250")
    if response:
        display_radar_status(response)
    
    utime.sleep_ms(500)
    
    print("\n[TEST 6] SET_VELOCITY - Simulate new velocity reading (8.5 m/s)")
    response = send_command("SET_VELOCITY", "8.5")
    if response:
        display_radar_status(response)
    
    utime.sleep_ms(500)
    
    print("\n[TEST 7] READ - Get updated sensor readings")
    response = send_command("READ")
    if response:
        display_radar_status(response)

def run_continuous_loop():
    """Run continuous sensor monitoring loop"""
    iteration = 0
    
    while True:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"CONTINUOUS MONITORING - Iteration {iteration}")
        print(f"{'='*60}")
        
        # Run READ command continuously
        response = send_command("READ")
        if response:
            display_radar_status(response)
        
        # Wait before next read
        print("Waiting 2 seconds for next read... (Press Ctrl+C to stop)")
        utime.sleep_ms(2000)

def run_interactive_mode():
    """Interactive command testing"""
    print("\n" + "=" * 60)
    print("INTERACTIVE MODE - Enter commands")
    print("=" * 60)
    print("Available commands:")
    print("  ping                    - Check if radar is alive")
    print("  whoami                  - Get device info")
    print("  read                    - Read current values")
    print("  status                  - Get detailed status")
    print("  range <value>           - Set distance (cm)")
    print("  velocity <value>        - Set velocity (m/s)")
    print("  test                    - Run full test sequence")
    print("  exit                    - Exit test")
    print("=" * 60)
    print()
    
    while True:
        try:
            cmd_line = input("radar> ").strip()
            
            if not cmd_line:
                continue
            
            parts = cmd_line.split()
            cmd = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else ""
            
            if cmd == "EXIT":
                print("Exiting test...")
                break
            elif cmd == "TEST":
                run_test_sequence()
            elif cmd == "PING":
                response = send_command("PING")
                if response:
                    display_radar_status(response)
            elif cmd == "WHOAMI":
                response = send_command("WHOAMI")
                if response:
                    display_radar_status(response)
            elif cmd == "READ":
                response = send_command("READ")
                if response:
                    display_radar_status(response)
            elif cmd == "STATUS":
                response = send_command("STATUS")
                if response:
                    display_radar_status(response)
            elif cmd == "RANGE" and arg:
                response = send_command("SET_RANGE", arg)
                if response:
                    display_radar_status(response)
            elif cmd == "VELOCITY" and arg:
                response = send_command("SET_VELOCITY", arg)
                if response:
                    display_radar_status(response)
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'test' for full test sequence or 'exit' to quit")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

# Main - Continuous Testing Loop
print("\nRadar Pico Firmware Test")
print(f"Device: {DEVICE_NAME}")
print(f"UART Baud Rate: 115200")
print()

try:
    # Show menu
    print("=" * 60)
    print("TEST MODE SELECTION")
    print("=" * 60)
    print("1. One-time test sequence (all 7 tests once)")
    print("2. Continuous READ loop (stream sensor data forever)")
    print("3. Interactive command mode")
    print("=" * 60)
    print("\nDefault: Press Enter for Continuous Loop")
    print()
    
    try:
        mode = input("Select mode (1/2/3) [default=2]: ").strip()
        if not mode:
            mode = "2"
    except:
        mode = "2"
    
    if mode == "1":
        print("\nRunning one-time test sequence...")
        run_test_sequence()
        print("\n" + "=" * 60)
        print("Test sequence completed!")
        print("=" * 60)
    
    elif mode == "2":
        print("\nStarting continuous loop...")
        print("This will keep running until you press Ctrl+C")
        print()
        run_continuous_loop()
    
    elif mode == "3":
        print("\nEntering interactive mode...")
        run_interactive_mode()
    
    else:
        print(f"Invalid mode '{mode}'. Running continuous loop by default...")
        print()
        run_continuous_loop()

except KeyboardInterrupt:
    print("\n\n" + "=" * 60)
    print("Test interrupted by user (Ctrl+C)")
    print("=" * 60)
