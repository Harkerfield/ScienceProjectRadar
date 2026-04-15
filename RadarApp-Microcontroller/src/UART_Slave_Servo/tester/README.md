# i2c_Slave_Servo - Tester Folder

## Testing Linear Servo Control with JSON API

This folder contains test code for the linear servo module controlled via PWM.
All communication uses standardized JSON format for responses.

### Available Tests

#### `test_servo_control.py`
Interactive menu for testing servo open/close functionality.
- **Commands:**
  - `1` - Open servo to full extension
  - `2` - Close servo to full retraction
  - `3` - Exit program

### Configuration
- **PIN:** GPIO 2
- **Frequency:** 50Hz
- **open duty:** 6553 (fully extended)
- **close duty:** 3277 (fully retracted)

### Wiring
- Brown wire: Ground (GND)
- Red wire: 5-6V DC Power
- Yellow wire: PWM Signal to GPIO 2

### JSON API Response Examples

All responses follow JSON format:
```json
{"s":"ok","msg":"opened","pos":100}   # Servo opened
{"s":"ok","msg":"closed","pos":0}     # Servo closed
{"s":"ok","state":"open","pos":100}   # Status check
{"s":"ok","msg":"alive","addr":"0x12"} # ping response
{"s":"error","msg":"unknown_command"}   # Error
```

### I2C Master Integration

**Example Python Code:**
```python
import smbus2

bus = smbus2.SMBus(1)
servo_ADDR = 0x12

# Open servo
bus.write_i2c_block_data(servo_ADDR, 0, list(b'open'))
response = bus.read_i2c_block_data(servo_ADDR, 0, 32)
resp_json = bytes(response).decode().rstrip('\x00')
print(f"Response: {resp_json}")
# Output: {"s":"ok","msg":"opened","pos":100}
```

### Usage
1. Run `test_servo_control.py` on the Pico
2. Select 1 to open or 2 to close
3. Motor will automatically set to the target position
4. Use Ctrl+C or option 3 to exit
