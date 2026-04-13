# i2c_Slave_Stepper - Tester Folder

## Testing NEMA Stepper Motor with Home Calibration & JSON API

This folder contains test code for stepper motor control with inductive home sensor calibration.
All communication uses standardized JSON format for responses.

### Available Tests

#### `test_stepper_home_calibration.py`
Comprehensive stepper motor testing and home position calibration.
- **Features:**
  - Home position finding and locking
  - Sensor transition detection
  - Multiple rotation speeds
  - Auto-return to home functionality
  - Gear ratio configuration checker

**Menu Options:**
1. Find and lock home position
2. Spin until home SENSOR triggers (auto-stop)
3. Spin 3 revolutions at custom speed
4. Spin & auto-return to start
5. Rotate to 180° then return to home
6. Spin indefinitely until Ctrl+C
7. Check gear ratio configuration
8. Exit

### Configuration
- **Motor Pins:**
  - GPIO 5: Pulse (PUL)
  - GPIO 6: Direction (DIR)
  - GPIO 7: Enable (ENA)
- **Sensor Pin:** GPIO 20 (inductive PNP sensor, active LOW)
- **Motor:** NEMA stepper, 200 steps/revolution
- **Gearing:** 20T→60T = 3:1 reduction (600 steps/revolution, 0.6°/step)
- **Frequency:** 50Hz controller

### Wiring
**Motor Control (DRV8825 stepper driver):**
- Motor GND → Pico GND
- Motor VCC → 5V
- Motor STEP → GPIO 5
- Motor DIR → GPIO 6
- Motor ENA → GPIO 7

**Home Sensor (3-wire inductive):**
- Brown: 6-36V DC power
- Blue: GND
- Black: GPIO 20 (active LOW when metal detected)

**Metal Target:**
- Mount small metal object on rotating shaft
- Position sensor to detect target once per revolution

### Usage
1. Mount inductive sensor and metal target correctly
2. Run `test_stepper_home_calibration.py` on the Pico
3. Select option 1 to find and lock home position
4. Motor will search in selected direction until sensor triggers
5. Use other options to test movement and speeds

### JSON API Response Examples

All responses follow JSON format:
```json
{"s":"ok","pos":45.0}              # Movement success
{"s":"ok","pos":0,"calib":1}       # Home calibration complete
{"s":"ok","speed":2000}            # Speed set to 2000µs
{"s":"error","msg":"not_calibrated"}  # Error
```

### Troubleshooting
- **Motor doesn't spin:** Check power supply and GPIO pin configuration
- **Sensor not detected:** Verify wiring, ensure metal target is positioned correctly
- **Motor spins wrong direction:** Adjust gearing configuration in code or swap DIR wire
- **Random direction changes:** Fixed with 10ms direction setup delay (already applied)
- **Weak holding torque:** Increase timeout between pulses (slower speed, larger µs value)
