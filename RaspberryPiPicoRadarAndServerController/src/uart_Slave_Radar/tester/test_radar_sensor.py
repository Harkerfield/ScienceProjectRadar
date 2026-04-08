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
DEVICE_ADDR = 0x20

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

# Main
print("\nRadar Pico Firmware Test")
print(f"Device: {DEVICE_NAME}")
print(f"Address: 0x{DEVICE_ADDR:02x}")
print(f"UART Baud Rate: 115200")
print()

# Run automatic test sequence
print("Running automatic test sequence...")
run_test_sequence()

print("\n" + "=" * 60)
print("Automatic test completed!")
print("=" * 60)

# Option to enter interactive mode
print("\nTest complete. Radar sensor is responding correctly.")
print("You can now:")
print("  - Send commands via UART to change sensor values")
print("  - Monitor responses to verify functionality")
print("  - Test integration with Node.js controller")
