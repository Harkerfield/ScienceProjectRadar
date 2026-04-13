# Stepper Motor Controller - JSON API Documentation

## Overview
All responses from the stepper motor slave (0x10) are now in compact JSON format.

## Response Format

### Success Response
```json
{"s":"ok","key1":value1,"key2":"value2"}
```

### Error Response
```json
{"s":"error","msg":"error_code"}
```

## Commands & Responses

### Motor Control

#### FIND_home - Calibrate Home Position
**Request:** `FIND_home`  
**Response:** `{"s":"ok","pos":0,"calib":1}`

#### move:<angle> - Move to Absolute Angle
**Request:** `move:90`  
**Response:** `{"s":"ok","pos":90.0}`

#### rotate:<degrees> - Rotate by Relative Amount
**Request:** `rotate:45`  
**Response:** `{"s":"ok","pos":45.0}`

#### START_rotate:<direction> - Continuous Rotation
**Request:** `START_rotate:CW` or `START_rotate:CCW`  
**Response:** `{"s":"ok","msg":"rotating","dir":"CW"}`

#### stop_rotate - Stop Continuous Rotation
**Request:** `stop_rotate`  
**Response:** `{"s":"ok","pos":90.0,"rev":2,"total":810.0}`

### Status & Configuration

#### status - Full System Status
**Request:** `status`  
**Response:** 
```json
{
  "s":"ok",
  "pos":45.0,
  "home":0,
  "sensor":0,
  "calib":1,
  "enabled":1,
  "speed":2000
}
```

#### POSITION - Current Position Only
**Request:** `POSITION`  
**Response:** 
```json
{
  "s":"ok",
  "pos":45.0,
  "rev":1,
  "total":405.0,
  "calib":1
}
```

#### AT_home - Check Home Status
**Request:** `AT_home`  
**Response:** `{"s":"ok","at_home":1}`

#### SENSOR - Single Sensor Read
**Request:** `SENSOR`  
**Response:** `{"s":"ok","sensor":0}`

### Speed Control

#### speed:<microseconds> - Set Motor Speed
**Request:** `speed:2000`  
**Response:** `{"s":"ok","speed":2000}`

Valid range: 500µs (fast) to 10000µs (slow)

### Monitoring & Diagnostics

#### ping - Heartbeat Check
**Request:** `ping`  
**Response:** `{"s":"ok","hb":5234,"uptime":10234,"addr":"0x10"}`

- `hb` = Heartbeat counter (incremented each loop)
- `uptime` = Milliseconds since slave started
- `addr` = Slave I2C address

### Motor Enable/Disable

#### enable - Enable Motor
**Request:** `enable`  
**Response:** `{"s":"ok","msg":"motor_enabled"}`

#### disable - Disable Motor
**Request:** `disable`  
**Response:** `{"s":"ok","msg":"motor_disabled"}`

## Error Codes

| Code | Meaning |
|------|---------|
| `not_calibrated` | Must run FIND_home first |
| `home_not_found` | Sensor not triggered during calibration |
| `speed_out_of_range` | Speed outside 500-10000 µs range |
| `invalid_move_format` | Command format error |
| `invalid_rotate_format` | Command format error |
| `invalid_direction` | Direction must be CW or CCW |
| `invalid_speed_format` | Speed value not an integer |
| `not_rotating` | stop_rotate called but not rotating |
| `unknown_command` | Command not recognized |

## I2C Protocol

### Heartbeat Monitoring (Memory-Based)
Bytes [0:4] of I2C memory contain a little-endian u32 heartbeat counter that increments every loop iteration.

**Master Example (Python):**
```python
import smbus2, struct

bus = smbus2.SMBus(1)
data = bus.read_i2c_block_data(0x10, 0, 4)
hb = struct.unpack('<I', bytes(data))[0]
print(f"Heartbeat: {hb}")
```

### Command Transmission
Send ASCII command string to slave I2C address 0x10, then read response.

**Example (Python):**
```python
bus.write_i2c_block_data(0x10, 0, list(b'status'))
response = bus.read_i2c_block_data(0x10, 0, 32)
response_str = bytes(response).decode().rstrip('\x00')
print(f"Response: {response_str}")
```

## Key Abbreviations in JSON

| Key | Full Name | Unit |
|-----|-----------|------|
| `s` | status | - |
| `pos` | position | degrees |
| `home` | at_home | 0=false, 1=true |
| `sensor` | sensor_state | 0=triggered, 1=clear |
| `calib` | calibrated | 0=false, 1=true |
| `enabled` | motor_enabled | 0=false, 1=true |
| `speed` | pulse_speed | microseconds |
| `hb` | heartbeat_counter | counter value |
| `uptime` | uptime_ms | milliseconds |
| `rev` | revolutions | count |
| `msg` | message/error | string |

## Hardware Configuration

**Motor Driver:** TB6600 with microstepping support  
**Motor:** NEMA17 with 3:1 gear reduction (600 steps/revolution)  
**Pins:**
- GPIO 5 = Pulse (PUL)
- GPIO 6 = Direction (DIR)
- GPIO 7 = Enable (ENA)
- GPIO 8-10 = Microstepping mode (MS1, MS2, MS3)
- GPIO 20 = Home sensor input

**Default Speeds:**
- Initial: 2000 µs (slow, good holding torque)
- Fine-tune: 3000 µs (slowest approach)
- Range: 500 µs (fast) to 10000 µs (very slow)

## Examples

### Basic Workflow
```
1. enable              → {"s":"ok","msg":"motor_enabled"}
2. FIND_home           → {"s":"ok","pos":0,"calib":1}
3. MOTION:90           → {"s":"ok","pos":90.0}
4. POSITION            → {"s":"ok","pos":90.0,"calib":1}
5. disable             → {"s":"ok","msg":"motor_disabled"}
```

### Continuous Rotation Workflow
```
1. FIND_home           → {"s":"ok","pos":0,"calib":1}
2. START_rotate:CW     → {"s":"ok","msg":"rotating","dir":"CW"}
3. POSITION            → {"s":"ok","pos":45.0,"rev":0,"total":45.0}
4. stop_rotate         → {"s":"ok","pos":90.0,"rev":1,"total":450.0}
```

### Speed Adjustment
```
1. speed:5000          → {"s":"ok","speed":5000}
2. move:180            → {"s":"ok","pos":180.0}
3. speed:2000          → {"s":"ok","speed":2000}
```

## I2C Master Integration

The Master API (`src/i2c_Master_API/main.py`) provides:

- `parse_json_response()` - Converts JSON bytes to Python dict
- `check_slave_online()` - Verifies slave is responding via ping
- `check_all_slaves()` - Monitors all connected slaves
- CRUD operations with automatic JSON parsing

All slave responses are automatically parsed into Python dictionaries for easy integration with server APIs.
