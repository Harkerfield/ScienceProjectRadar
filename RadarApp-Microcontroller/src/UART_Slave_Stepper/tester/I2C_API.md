# Stepper Motor I2C Slave API Documentation

## Overview

The Stepper Pico operates as an I2C slave device at address **0x10** (decimal 16). It implements a binary protocol for CRUD operations on motor settings, status queries, and action commands.

All communication is big-endian (most significant byte first).

---

## I2C Device Information

- **Slave Address:** `0x10` (0x08 on 7-bit addressing)
- **Protocol:** I2C/TWI binary protocol
- **Memory Buffer:** 256 bytes
- **Response Time:** Immediate (handled via IRQ callback)

---

## Command Protocol

### Command Structure

All commands follow this format:

```
[COMMAND_BYTE] [PARAM_1] [PARAM_2] ... [PARAM_N]
```

### Command Types

| Command | Hex | Purpose | Parameters | Response |
|---------|-----|---------|-----------|----------|
| SET | 0x01 | Set a configuration setting | [SETTING_ID][VALUE_BYTES] | [status] |
| GET | 0x02 | Get a configuration setting | [SETTING_ID] | [status][VALUE_BYTES] |
| status | 0x03 | Get all settings (bulk read) | None | [status][ALL_SETTINGS] |
| ACTION | 0x04 | Execute a motor action | [ACTION_ID][PARAMS] | [status] |
| HEARTBEAT | 0x05 | Verify slave is online | None | [0x01][COUNTER_HI][COUNTER_LO] |

---

## Settings (CRUD Operations)

### Setting IDs and Types

| ID | Hex | Name | Type | Range | R/W | Description |
|----|-----|------|------|-------|-----|-------------|
| 1 | 0x01 | direction | uint8 | 0-1 | RW | 0=CCW, 1=CW |
| 2 | 0x02 | speed | uint16 | 100-2000 | RW | Pulse duration in microseconds (lower=faster) |
| 3 | 0x03 | acceleration | uint16 | 0-1000 | RW | Acceleration factor (0=disabled) |
| 4 | 0x04 | home_position | uint16 | 0-360 | RW | Home position in degrees |
| 5 | 0x05 | max_speed | uint16 | 100-500 | RW | Maximum speed (minimum pulse time µs) |
| 6 | 0x06 | min_speed | uint16 | 500-5000 | RW | Minimum speed (maximum pulse time µs) |
| 7 | 0x07 | enabled | uint8 | 0-1 | RW | Motor enable: 0=disabled, 1=enabled |
| 16 | 0x10 | position | uint16 | 0-360 | RO | Current motor position in degrees |
| 17 | 0x11 | at_home | uint8 | 0-1 | RO | At home status: 0=not home, 1=at home |
| 18 | 0x12 | sensor_state | uint8 | 0-1 | RO | Sensor state: 0=triggered, 1=clear |

**Note:** RO = Read-Only, RW = Read-Write

---

## Command Details & Examples

### 1. SET Command (0x01)

**Set a configuration value on the slave.**

#### Format
```
[0x01] [SETTING_ID] [VALUE_BYTES...]
```

#### Value Byte Lengths
- **1-byte settings:** direction, enabled, at_home, sensor_state
- **2-byte settings:** speed, acceleration, home_position, max_speed, min_speed, position

#### Examples

**Set Direction to Clockwise:**
```
Request:  [0x01] [0x01] [0x01]
Response: [0x01]
Meaning:  Set direction (0x01) = 1 (CW)
```

**Set Speed to 500µs:**
```
Request:  [0x01] [0x02] [0x01] [0xF4]
Response: [0x01]
Meaning:  Set speed (0x02) = 0x01F4 = 500 (microseconds)
```

**Set Home Position to 0°:**
```
Request:  [0x01] [0x04] [0x00] [0x00]
Response: [0x01]
Meaning:  Set home_position (0x04) = 0x0000 = 0 degrees
```

**Enable Motor:**
```
Request:  [0x01] [0x07] [0x01]
Response: [0x01]
Meaning:  Set enabled (0x07) = 1 (motor on)
```

---

### 2. GET Command (0x02)

**Retrieve a configuration value from the slave.**

#### Format
```
[0x02] [SETTING_ID]
```

#### Response Format
```
[status] [VALUE_BYTES...]
```

#### Examples

**Get Current Direction:**
```
Request:  [0x02] [0x01]
Response: [0x01] [0x01]
Meaning:  Status OK, direction = 1 (CW)
```

**Get Current Speed:**
```
Request:  [0x02] [0x02]
Response: [0x01] [0x01] [0xF4]
Meaning:  Status OK, speed = 0x01F4 = 500µs
```

**Get Current Position:**
```
Request:  [0x02] [0x10]
Response: [0x01] [0x00] [0xB4]
Meaning:  Status OK, position = 0x00B4 = 180 degrees
```

**Get Motor Enabled Status:**
```
Request:  [0x02] [0x07]
Response: [0x01] [0x01]
Meaning:  Status OK, enabled = 1 (motor is on)
```

**Get At Home Status (Read-Only):**
```
Request:  [0x02] [0x11]
Response: [0x01] [0x01]
Meaning:  Status OK, at_home = 1 (motor is at home)
```

**Get Sensor State (Read-Only):**
```
Request:  [0x02] [0x12]
Response: [0x01] [0x01]
Meaning:  Status OK, sensor_state = 1 (clear, no metal detected)
```

---

### 3. status Command (0x03)

**Get all settings and current status in one bulk read.**

#### Format
```
[0x03]
```

#### Response Format
```
[status] [BULK_DATA...]
```

Response data (12 bytes):
```
[0]    Position MSB (uint16)
[1]    Position LSB
[2]    At Home (uint8)
[3]    Sensor State (uint8)
[4]    Direction (uint8)
[5]    Speed MSB (uint16)
[6]    Speed LSB
[7]    Enabled (uint8)
[8]    Home Position MSB (uint16)
[9]    Home Position LSB
[10]   Acceleration MSB (uint16)
[11]   Acceleration LSB
```

#### Example

**Get All Status:**
```
Request:  [0x03]
Response: [0x01] [0x00] [0xB4] [0x01] [0x01] [0x01] [0x01] [0xF4] [0x01] [0x00] [0x00] [0x00] [0x00]
Meaning:  OK | Pos=180° | AtHome=1 | Sensor=1(clear) | Dir=1(CW) | Speed=500µs | Enabled=1 | HomePos=0° | Accel=0
```

---

### 4. ACTION Command (0x04)

**Execute a motor action (move, home, enable, disable).**

#### Format
```
[0x04] [ACTION_ID] [PARAMS...]
```

#### Action Types

| Action | Hex | Parameters | Description |
|--------|-----|-----------|-------------|
| move | 0x01 | [ANGLE_MSB][ANGLE_LSB] | Move to specified angle (0-360°) |
| home | 0x02 | None | Find and lock home position |
| enable | 0x03 | None | Enable motor driver |
| disable | 0x04 | None | Disable motor driver |

#### Examples

**Move to 90 degrees:**
```
Request:  [0x04] [0x01] [0x00] [0x5A]
Response: [0x01]
Meaning:  Action move to 0x005A = 90 degrees. Status OK.
```

**Move to 180 degrees:**
```
Request:  [0x04] [0x01] [0x00] [0xB4]
Response: [0x01]
Meaning:  Action move to 0x00B4 = 180 degrees. Status OK.
```

**Find Home:**
```
Request:  [0x04] [0x02]
Response: [0x01]
Meaning:  Action FIND home started. Status OK when complete.
```

**Enable Motor:**
```
Request:  [0x04] [0x03]
Response: [0x01]
Meaning:  Motor enabled. Status OK.
```

**Disable Motor:**
```
Request:  [0x04] [0x04]
Response: [0x01]
Meaning:  Motor disabled. Status OK.
```

---

### 5. HEARTBEAT Command (0x05)

**Verify that the slave is online and responsive.**

#### Format
```
[0x05]
```

#### Response Format
```
[0x01] [COUNTER_MSB] [COUNTER_LSB]
```

**Response Bytes:**
- **[0]:** Status code (always 0x01 for success)
- **[1-2]:** Heartbeat counter (uint16) - incremented each time heartbeat is called

#### Purpose

This command allows the master to:
- Verify the slave device is powered and online
- Detect I2C bus or communication failures
- Monitor slave availability over time via the counter

#### Example

**First Heartbeat Request:**
```
Request:  [0x05]
Response: [0x01] [0x00] [0x01]
Meaning:  Status OK, heartbeat counter = 1
```

**Subsequent Heartbeat Requests:**
```
Request:  [0x05]
Response: [0x01] [0x00] [0x02]
Meaning:  Status OK, heartbeat counter = 2
```

**Recommended Usage:**

Master should send heartbeat at regular intervals (e.g., 100ms - 1s) to detect communication failures. 
- If no response: Slave is offline or I2C bus is faulty
- If counter stops incrementing: Slave firmware may have crashed
- Counter reset to 1: Slave has been rebooted

---

## Response Status Codes

| Code | Hex | Meaning |
|------|-----|---------|
| SUCCESS | 0x01 | Command executed successfully |
| error | 0xFF | Command failed or invalid |

---

## Data Types & Byte Ordering

All multi-byte values use **big-endian (network) byte order** (most significant byte first).

### Integer Encoding Examples

**uint8 (1 byte):**
```
Value: 1        → [0x01]
Value: 255      → [0xFF]
```

**uint16 (2 bytes):**
```
Value: 0        → [0x00] [0x00]
Value: 256      → [0x01] [0x00]
Value: 500      → [0x01] [0xF4]
Value: 360      → [0x01] [0x68]
Value: 65535    → [0xFF] [0xFF]
```

---

## Complete CRUD Example Workflow

### Scenario: Configure stepper, move to position, check status

```
1. SET Speed to 500µs
   Request:  [0x01] [0x02] [0x01] [0xF4]
   Response: [0x01]
   
2. SET Direction to CW
   Request:  [0x01] [0x01] [0x01]
   Response: [0x01]
   
3. enable Motor
   Request:  [0x04] [0x03]
   Response: [0x01]
   
4. move to 90°
   Request:  [0x04] [0x01] [0x00] [0x5A]
   Response: [0x01]
   
5. GET Current Position
   Request:  [0x02] [0x10]
   Response: [0x01] [0x00] [0x5A]  (confirms at 90°)
   
6. GET Status
   Request:  [0x03]
   Response: [0x01] [0x00] [0x5A] [0x01] [0x01] [0x01] [0x01] [0xF4] [0x01] [0x00] [0x00] [0x00] [0x00]
   
7. FIND home
   Request:  [0x04] [0x02]
   Response: [0x01]  (blocks until home found)
   
8. GET At Home Status
   Request:  [0x02] [0x11]
   Response: [0x01] [0x01]  (confirms at home)
```

---

## Motor Configuration

### Stepper Motor Specs
- **Motor Type:** NEMA stepper (bipolar)
- **Steps per Revolution:** 200
- **Degrees per Step:** 1.8°

### Gearing
- **Configuration:** 20-tooth (motor) → 60-tooth (output) = 3:1 reduction
- **Output Steps per Revolution:** 600
- **Output Degrees per Step:** 0.6°

### GPIO Pinouts
- **GPIO 5:** PUL (Pulse) - PWM step signal
- **GPIO 6:** DIR (Direction) - High=CW, Low=CCW
- **GPIO 7:** ENA (Enable) - High=enabled, Low=disabled

### Home Sensor
- **GPIO 20:** Inductive Proximity Sensor (OMRON LJ12A3-4Z/BY)
- **Type:** PNP (sinking input)
- **Detection:** LOW (0) when metal detected
- **Default:** HIGH (1) when clear

---

## Speed Configuration Guide

### Pulse Duration (Speed) Recommendations

| Duration | Speed Label | Use Case |
|----------|------------|----------|
| 100µs | Maximum | Fastest rotation, lowest torque |
| 130µs | Max (Fast) | Fast scanning operations |
| 500µs | Medium | Balanced speed/torque, default |
| 1000µs | Low | Slowest, maximum torque |
| 2000µs | Very Low | Precise slow movement |

**Formula:** Speed (RPM) ≈ 1,000,000 / (pulse_time × 600)

Example: 500µs pulse → ~3.3 RPM at output

---

## Error Handling

### Common Errors

**Setting Read-Only Property:**
```
Request:  [0x01] [0x10] [0x01]  (try to SET position)
Response: [0xFF]
```

**Invalid Setting ID:**
```
Request:  [0x02] [0xFF]
Response: [0xFF]
```

**Invalid Command:**
```
Request:  [0x05] [0x00]
Response: [0xFF]
```

**Incomplete Command:**
```
Request:  [0x01] [0x02]  (missing value bytes)
Response: [0xFF]
```

---

## Python Example (Master Side)

```python
import smbus
import time

# Create I2C bus interface
bus = smbus.SMBus(1)  # Bus 1 on Raspberry Pi
stepper_ADDR = 0x10

# SET speed to 500µs
def set_speed(speed_us):
    data = [0x01, 0x02, (speed_us >> 8) & 0xFF, speed_us & 0xFF]
    bus.write_i2c_block_data(stepper_ADDR, 0, data)
    response = bus.read_i2c_block_data(stepper_ADDR, 0, 1)
    return response[0] == 0x01

# GET current position
def get_position():
    bus.write_i2c_block_data(stepper_ADDR, 0, [0x02, 0x10])
    response = bus.read_i2c_block_data(stepper_ADDR, 0, 3)
    if response[0] == 0x01:
        position = (response[1] << 8) | response[2]
        return position
    return None

# ACTION: move to angle
def move_to(angle):
    data = [0x04, 0x01, (angle >> 8) & 0xFF, angle & 0xFF]
    bus.write_i2c_block_data(stepper_ADDR, 0, data)
    response = bus.read_i2c_block_data(stepper_ADDR, 0, 1)
    return response[0] == 0x01

# ACTION: FIND home
def find_home():
    bus.write_i2c_block_data(stepper_ADDR, 0, [0x04, 0x02])
    response = bus.read_i2c_block_data(stepper_ADDR, 0, 1)
    return response[0] == 0x01

# Get all status
def get_all_status():
    bus.write_i2c_block_data(stepper_ADDR, 0, [0x03])
    response = bus.read_i2c_block_data(stepper_ADDR, 0, 13)
    if response[0] == 0x01:
        return {
            'position': (response[1] << 8) | response[2],
            'at_home': response[3],
            'sensor_state': response[4],
            'direction': response[5],
            'speed': (response[6] << 8) | response[7],
            'enabled': response[8],
            'home_position': (response[9] << 8) | response[10],
            'acceleration': (response[11] << 8) | response[12],
        }
    return None

# Example usage
if __name__ == '__main__':
    set_speed(500)
    print(f"Position: {get_position()}°")
    move_to(90)
    time.sleep(2)
    print(f"Status: {get_all_status()}")
```

---

## JavaScript Example (Web/Node.js Master Side)

```javascript
// Requires i2c-bus package: npm install i2c-bus

const i2c = require('i2c-bus');
const bus = i2c.openSync(1); // Bus 1
const stepper_ADDR = 0x10;

// SET speed to 500µs
async function setSpeed(speedUs) {
    const data = Buffer.from([0x01, 0x02, (speedUs >> 8) & 0xFF, speedUs & 0xFF]);
    await bus.i2cWrite(stepper_ADDR, data.length, data);
    const response = Buffer.alloc(1);
    await bus.i2cRead(stepper_ADDR, 1, response);
    return response[0] === 0x01;
}

// GET current position
async function getPosition() {
    const cmd = Buffer.from([0x02, 0x10]);
    await bus.i2cWrite(stepper_ADDR, cmd.length, cmd);
    const response = Buffer.alloc(3);
    await bus.i2cRead(stepper_ADDR, 3, response);
    if (response[0] === 0x01) {
        return (response[1] << 8) | response[2];
    }
    return null;
}

// ACTION: move to angle
async function moveTo(angle) {
    const data = Buffer.from([0x04, 0x01, (angle >> 8) & 0xFF, angle & 0xFF]);
    await bus.i2cWrite(stepper_ADDR, data.length, data);
    const response = Buffer.alloc(1);
    await bus.i2cRead(stepper_ADDR, 1, response);
    return response[0] === 0x01;
}

// ACTION: FIND home
async function findHome() {
    const cmd = Buffer.from([0x04, 0x02]);
    await bus.i2cWrite(stepper_ADDR, cmd.length, cmd);
    const response = Buffer.alloc(1);
    await bus.i2cRead(stepper_ADDR, 1, response);
    return response[0] === 0x01;
}

// Get all status
async function getAllStatus() {
    const cmd = Buffer.from([0x03]);
    await bus.i2cWrite(stepper_ADDR, cmd.length, cmd);
    const response = Buffer.alloc(13);
    await bus.i2cRead(stepper_ADDR, 13, response);
    
    if (response[0] === 0x01) {
        return {
            position: (response[1] << 8) | response[2],
            atHome: response[3],
            sensorState: response[4],
            direction: response[5],
            speed: (response[6] << 8) | response[7],
            enabled: response[8],
            homePosition: (response[9] << 8) | response[10],
            acceleration: (response[11] << 8) | response[12],
        };
    }
    return null;
}

// Example usage
(async () => {
    await setSpeed(500);
    console.log(`Position: ${await getPosition()}°`);
    await moveTo(90);
    await new Promise(r => setTimeout(r, 2000));
    console.log(`Status: ${JSON.stringify(await getAllStatus())}`);
    bus.closeSync();
})();
```

---

## Troubleshooting

### Motor Not Responding
1. Verify I2C address: `i2cdetect -y 1`
2. Check GPIO connections
3. Ensure 3.3V/GND power connections
4. Test with simple status command (0x03)

### Sensor Not Detecting
1. Verify GPIO 20 wiring
2. Check sensor power (Brown wire 6-36V)
3. Position metal target within 5-10mm of sensor
4. Read sensor_state (0x12) to verify detection

### Motor Moving Incorrectly
1. Check DIR pin (GPIO 6)
2. Verify direction setting with GET command
3. Confirm speed isn't too high (try 1000µs)
4. Check for stalled stepper (not enough current)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-04 | Initial binary protocol documentation |

---

## License & Support

For issues, improvements, or questions about this API:
- Check the main.py source code for implementation details
- Review test_stepper_home_calibration.py for testing examples
- Consult stepper motor and I2C documentation

