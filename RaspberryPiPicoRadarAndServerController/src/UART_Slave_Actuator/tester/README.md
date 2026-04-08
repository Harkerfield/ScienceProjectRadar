# i2c_Slave_Actuator - Tester Folder

## Testing Linear Actuator Control with JSON API

This folder contains test code for the linear actuator module controlled via PWM.
All communication uses standardized JSON format for responses.

### Available Tests

#### `test_actuator_control.py`
Interactive menu for testing actuator open/close functionality.
- **Commands:**
  - `1` - Open actuator to full extension
  - `2` - Close actuator to full retraction
  - `3` - Exit program

### Configuration
- **PIN:** GPIO 2
- **Frequency:** 50Hz
- **OPEN duty:** 6553 (fully extended)
- **CLOSE duty:** 3277 (fully retracted)

### Wiring
- Brown wire: Ground (GND)
- Red wire: 5-6V DC Power
- Yellow wire: PWM Signal to GPIO 2

### JSON API Response Examples

All responses follow JSON format:
```json
{"s":"ok","msg":"opened","pos":100}   # Actuator opened
{"s":"ok","msg":"closed","pos":0}     # Actuator closed
{"s":"ok","state":"open","pos":100}   # Status check
{"s":"ok","msg":"alive","addr":"0x12"} # PING response
{"s":"error","msg":"unknown_command"}   # Error
```

### I2C Master Integration

**Example Python Code:**
```python
import smbus2

bus = smbus2.SMBus(1)
ACTUATOR_ADDR = 0x12

# Open actuator
bus.write_i2c_block_data(ACTUATOR_ADDR, 0, list(b'OPEN'))
response = bus.read_i2c_block_data(ACTUATOR_ADDR, 0, 32)
resp_json = bytes(response).decode().rstrip('\x00')
print(f"Response: {resp_json}")
# Output: {"s":"ok","msg":"opened","pos":100}
```

### Usage
1. Run `test_actuator_control.py` on the Pico
2. Select 1 to open or 2 to close
3. Motor will automatically set to the target position
4. Use Ctrl+C or option 3 to exit
