
import serial
import time

ser = serial.Serial('/dev/ttyAMA0', 460800, timeout=2)
print("✓ Connected to Pico Master")

# Send a test ping command
print("\n→ Sending: servo:ping")
ser.write(b'servo:ping\n')

time.sleep(1)

# Try to read response
if ser.in_waiting:
    response = ser.read(ser.in_waiting).decode()
    print(f"← Received: {response}")
else:
    print("← No response received")

ser.close()
EOF