# HB100 Doppler Radar Sensor - Setup & Test Guide

This guide covers testing the HB100 10.525GHz Doppler Effect Microwave Motion Sensor with Raspberry Pi Pico.

## Hardware Overview

The HB100 is a 10.525GHz Doppler radar sensor that detects motion using the Doppler effect. As objects move toward or away from the sensor, the reflected microwave signal frequency shifts, indicating motion.

**Key Specs:**
- Operating Frequency: 10.525 GHz (fixed)
- Detection Range: ~5-7 meters typical
- Power Supply: 3.3V or 5V (check your module)
- Output: IF (Intermediate Frequency) signal
- No reflectors needed - works through most materials

## Pinout Reference

### Standalone HB100 Module
```
Pin 1: OUT/IF      → Pico ADC pin (GPIO27)
Pin 2: GND         → Pico GND
Pin 3: VCC         → Pico 3.3V or 5V
```

### CQRobot Version (SPR501)
May have additional pins:
```
Pin 1: GND         → Pico GND
Pin 2: VCC         → Pico 3.3V or 5V
Pin 3: OUT/IF      → Pico ADC pin (GPIO27)
Pin 4: DIR (optional) → Pico GPIO26 (motion direction)
```

## Wiring to Raspberry Pi Pico

### Standard Connection (Recommended)

```
HB100                  Pico
─────────────────────────────
VCC (3.3V)    ──────→ 3.3V (Pin 36)
GND           ──────→ GND (Pin 38)
IF/OUT        ──────→ GPIO27 (ADC1)
```

### With Optional Motion Pin (CQRobot)

```
HB100                  Pico
─────────────────────────────
VCC           ──────→ 3.3V (Pin 36)
GND           ──────→ GND (Pin 38)
IF/OUT        ──────→ GPIO27 (ADC1)
DIR/MOTION    ──────→ GPIO26
```

**Important:** 
- Use 3.3V for CQRobot version (has voltage regulator)
- Use appropriate power supply for standalone (check module)
- Keep IF/OUT wire short to minimize noise
- Shield IF wire if possible for cleaner readings

## Test Script Usage

### Loading the Test

1. **Connect your Pico** to your development computer
2. **Open `test_hb100_sensor.py`** in Thonny or MicroPython IDE
3. **Verify pinout** in the script matches your wiring
4. **Upload and run** the script

Expected startup:
```
======================================================================
HB100 DOPPLER RADAR SENSOR TEST
10.525GHz Microwave Motion Sensor (SKU: CQRSENWB01)
======================================================================

HB100 Configuration:
  IF Output Pin:     GPIO27 (ADC1)
  Motion Pin:        GPIO26
  Status LED:        GPIO25

Connections:
  HB100 VCC:         3.3V on Pico
  HB100 GND:         GND on Pico
  HB100 IF Output:   GPIO27 (ADC1)
  HB100 Motion:      GPIO26 (optional)
```

### Test Options

**1. Single Sample Test**
- Reads 5 sensor samples
- Shows ADC values and motion intensity
- Good for quick verification

**2. Raw ADC Stream** (Best for troubleshooting)
- Streams raw ADC values for 10 seconds
- Outputs in CSV format: `Time(ms), ADC_Raw, Voltage(V)`
- Copy output to analyze signal patterns
- Shows if sensor is working at all

**3. Continuous Test** (Good for motion detection)
- Monitors sensor for 30 seconds
- LED blinks when motion detected
- Shows direction estimation (approaching/receding)
- Try moving around sensor while running

**4. Sensitivity Test** (Calibration)
- Finds your system's motion threshold
- Records baseline (no motion) vs. motion readings
- Suggests optimal threshold value
- Use this to tune motion detection

**5. Calibration** (Setup)
- Records 10 seconds of baseline readings
- Shows ADC average, min, max, variation
- Use to understand your environment noise

## Interpreting Results

### ADC Raw Values
- **Standalone HB100:** 30,000-65,535 range typical
- **Still (no motion):** Values stable, low variation
- **Motion present:** Values fluctuate, high variation

### Voltage Reading
- **VCC = 3.3V:** Typical 0-3.3V range
- **IF signal offset:** Usually ~1.5V when stationary
- **Fluctuates 0.5-3.0V** with motion

### Intensity Percentage (0-100%)
- **0-10%:** No motion, environment noise
- **10-30%:** Subtle motion (slow movement far away)
- **30-70%:** Clear motion (person walking)
- **70-100%:** Strong motion (rapid movement close)

### Direction
- **Approaching:** Object moving toward sensor
- **Receding:** Object moving away
- **Stationary:** No net motion

## Troubleshooting

### Problem: No ADC Reading (stuck at 0 or 65535)

**Check:**
1. GPIO27 is not being used elsewhere
2. ADC pin connected to IF/OUT pin
3. Power supply to HB100 is stable
4. No shorts in wiring

**Solution:**
```python
# Verify ADC works
adc = machine.ADC(machine.Pin(27))
print(adc.read_u16())  # Should show changing values 1000-60000
```

### Problem: Reading Not Changing (stationary value)

**Possible causes:**
1. IF output pin is low impedance (needs buffering)
2. ADC is measuring noise rather than signal
3. Module may not be powered correctly

**Solution:**
- Run "Raw ADC Stream" test for 30 seconds
- Move hand slowly over sensor
- Look for ADC value changes
- Should see 5,000+ variation with motion

### Problem: Erratic or Noise Readings

**Causes:**
1. Long IF wire picking up interference
2. USB cable too close to sensor hardware
3. Poor power supply (USB ripple)

**Solutions:**
- Shorten IF wire (max 10cm recommended)
- Move USB away from HB100
- Use separate power supply if available
- Shield the IF wire with grounded foil

### Problem: No Motion Detected Even When Moving

**Check:**
1. Sensitivity threshold too high (run Sensitivity Test)
2. Moving too slowly (try faster motions)
3. Sensor range (typically 5-7m line of sight)
4. Antenna alignment (some versions directional)

**Solution:**
```python
# Lower threshold in script
sensor.motion_threshold = 50  # Lower = more sensitive
```

## Understanding Raw Output

### CSV Stream Format
```
Time(ms), ADC_Raw, Voltage(V)
0, 32768, 1.650
10, 32850, 1.655
20, 32925, 1.661
```

**Analysis:**
- Time: Milliseconds from test start
- ADC_Raw: 0-65535 (12-bit ADC is common, right-shifted)
- Voltage: Converted to 0-3.3V range

**Patterns:**
- **Flat line:** Sensor not responding or stuck
- **Slow drift:** Environmental interference
- **Oscillation 500-2000 counts:** Normal IF signal
- **Large swings 10,000+ counts:** Motion detected

## Connecting to Node.js Controller

Once verified with this test script, the HB100 can feed data to the Node.js server:

1. Modify `main.py` in `uart_Slave_Radar/` to read from GPIO27
2. Process ADC values to extract motion/direction
3. Send via UART to Node.js interface
4. Dashboard displays real-time radar data

**Next steps:**
- Test raw sensor with this script first
- Calibrate thresholds for your environment
- Integrate ADC reading code into radar firmware
- Test UART communication to Node.js

## Module Selection Guide

### Use Standalone HB100 if:
- Building custom interface
- Want lowest cost
- Have analog filtering capability
- Can manage 5V or 3.3V supply yourself

### Use CQRobot Version if:
- Want ready-to-use breakout
- Need regulated 3.3V power
- Want motion detection pin
- Prefer tested design

Both should work identically for motion detection once properly wired.

## Performance Tips

- **Sensitivity:** IF signal variation indicates motion intensity
- **Range:** ~5-7m typical, varies with size/reflectivity of target
- **Response time:** ~100-200ms to detect motion
- **False positives:** Reduce with threshold calibration
- **Power:** ~20-30mA typical draw

## Next: Integration

Once sensor works with this test:
1. Record your baseline/threshold values
2. Update `uart_Slave_Radar/main.py` to read GPIO27 instead of simulating
3. Process ADC into range/velocity estimates
4. Send results via UART protocol
5. Monitor in Node.js dashboard

See [README.md](README.md) for UART protocol details.
