# Pico Microcontroller API Specification
## Actual Implementation from Source Code Analysis

---

## 1. DEVICE ADDRESSING SCHEME

### Protocol Format
All devices use a **colon-delimited addressing scheme** on a shared UART1 bus (115200 baud):

```
REQUEST:  DEVICE:COMMAND[:ARGS]\n
RESPONSE: DEVICE:STATUS[:DATA]\n
```

### Device Identifiers
- **STEPPER** - Stepper motor controller (UART Slave)
- **SERVO** - Servo actuator (UART Slave) 
- **RADAR** - Radar sensor (UART Slave)

### Example Commands
```
STEPPER:PING
SERVO:OPEN
RADAR:READ
STEPPER:MOVE:90
```

---

## 2. STEPPER MOTOR CONTROLLER - COMPLETE API

### Device Name: `STEPPER`
**File Location:** `src/UART_Slave_Stepper/main.py`

#### Motor Hardware Configuration
- **Motor:** NEMA17 with 3:1 gear reduction = 600 steps/revolution
- **Degrees per step:** 0.6°
- **Speed Range:** 500µs (fastest) to 10,000µs (slowest)
- **Default Speed:** 2000µs (slow, good holding torque)
- **Fine-tune Speed:** 3000µs (approach to home)
- **Control Pins:** GPIO 5 (PUL), GPIO 6 (DIR), GPIO 7 (ENA)
- **Home Sensor:** GPIO 20 (inductive, PULL_UP, 1=triggered/home, 0=clear)

### Commands (UART Protocol)

#### Standard Commands

**PING - Alive Check**
```
Request:  STEPPER:PING
Response: STEPPER:OK:msg=alive:uptime=120s
```

**WHOAMI - Device Identification**
```
Request:  STEPPER:WHOAMI
Response: STEPPER:OK:device=STEPPER:type=motor_controller
```

**STATUS - Full System Status**
```
Request:  STEPPER:STATUS
Response: STEPPER:OK:state=HOME:position=0:calibrated=1

Response fields:
  - state: HOME | ROTATING | IDLE
  - position: current angle in degrees (0-360)
  - calibrated: 1=home calibrated, 0=not calibrated
```

#### Motor Control Commands

**HOME - Calibrate Home Position (2-Phase)**
```
Request:  STEPPER:HOME
Response: STEPPER:OK:msg=home_found:pos=0:calib=1
          OR
          STEPPER:ERROR:home_not_found

Behavior:
  Phase 1: Fast CCW search until sensor triggers (max 5 revolutions)
  Phase 2: Slow CW approach to fine-tune exact position
  - Position is set to exactly 0° after calibration
  - REQUIRED before MOVE or ROTATE commands
```

**MOVE - Move to Absolute Angle**
```
Request:  STEPPER:MOVE:90
Response: STEPPER:OK:msg=moved:pos=90:target=90
          OR
          STEPPER:ERROR:not_calibrated
          OR
          STEPPER:ERROR:move_failed

Parameters:
  - angle: 0-360 degrees (float)
  
Behavior:
  - Takes shortest path (CW or CCW)
  - Calculates optimal direction to minimize rotation
  - Updates internal position tracking
  - Requires home calibration first
```

**ROTATE - Rotate by Relative Amount**
```
Request:  STEPPER:ROTATE:45
Response: STEPPER:OK:msg=rotated:pos=45:delta=45
          OR
          STEPPER:ERROR:not_calibrated

Parameters:
  - delta: relative degrees (float, positive=CW, negative=CCW)

Behavior:
  - Rotates relative to current position
  - Positive = clockwise, Negative = counter-clockwise
  - Updates position tracking
  - Requires home calibration first
```

**SPIN - Start Continuous Rotation**
```
Request:  STEPPER:SPIN:2000
Response: STEPPER:OK:msg=spin_started:speed=2000:direction=CW
          OR
          STEPPER:ERROR:speed_required
          OR
          STEPPER:ERROR:speed_out_of_range:min=500:max=10000
          OR
          STEPPER:ERROR:invalid_speed

Parameters:
  - speed: pulse duration in microseconds (integer)
  
Valid Range: 500µs (fastest) to 10,000µs (slowest)

Behavior:
  - Starts continuous rotation in CW direction
  - Speed parameter sets pulse duration
  - Continues until STOP command received
  - Returns immediately (non-blocking)
  - Does not require home calibration
```

**STOP - Stop Continuous Rotation**
```
Request:  STEPPER:STOP
Response: STEPPER:OK:msg=stopped:pos=45:revolutions=2
          OR
          STEPPER:ERROR:not_rotating

Response fields:
  - pos: final position in degrees
  - revolutions: complete 360° rotations counted
```

**SPEED - Set or Get Motor Speed**
```
Request (GET):  STEPPER:SPEED
Response:       STEPPER:OK:msg=current_speed:speed=2000

Request (SET):  STEPPER:SPEED:2500
Response:       STEPPER:OK:msg=speed_set:speed=2500
                OR
                STEPPER:ERROR:speed_out_of_range:min=500:max=10000

Parameters:
  - speed: pulse duration in microseconds (integer)

Valid Range: 500µs to 10,000µs
```

**ENABLE - Enable Motor**
```
Request:  STEPPER:ENABLE
Response: STEPPER:OK:msg=enabled:enabled=1
```

**DISABLE - Disable Motor**
```
Request:  STEPPER:DISABLE
Response: STEPPER:OK:msg=disabled:enabled=0
```

#### Error Responses
```
STEPPER:ERROR:empty_command
STEPPER:ERROR:invalid_format
STEPPER:ERROR:wrong_device:<device_name>
STEPPER:ERROR:unknown_command:<cmd>
STEPPER:ERROR:command_error:<error_detail>
STEPPER:ERROR:buffer_overflow
```

---

## 3. SERVO ACTUATOR CONTROLLER API

### Device Name: `SERVO`
**File Location:** `src/UART_Slave_Actuator/main.py`

#### Hardware Configuration
- **Control:** PWM on GPIO 2 at 50Hz
- **Pulse Range:** Open (~2ms = duty_u16:6553) to Closed (~1ms = duty_u16:3276)
- **Movement Time:** 6 seconds (hard-coded wait)

### Commands (UART Protocol)

**PING - Alive Check**
```
Request:  SERVO:PING
Response: SERVO:OK:msg=alive:uptime=120s
```

**WHOAMI - Device Identification**
```
Request:  SERVO:WHOAMI
Response: SERVO:OK:device=SERVO:type=actuator
```

**STATUS - Current State**
```
Request:  SERVO:STATUS
Response: SERVO:OK:state=open:device=servo
          OR
          SERVO:OK:state=closed:device=servo

Response fields:
  - state: "open" or "closed" (lowercase)
  - device: always "servo"
```

**OPEN - Extend Actuator**
```
Request:  SERVO:OPEN
Response: SERVO:OK:msg=opened:state=open

Behavior:
  - Sets PWM duty to 2ms pulse (~6553 u16)
  - Waits 6 seconds for mechanical movement to complete
  - Updates internal state to "OPEN"
  - Returns after movement complete (blocking)
```

**CLOSE - Retract Actuator**
```
Request:  SERVO:CLOSE
Response: SERVO:OK:msg=closed:state=closed

Behavior:
  - Sets PWM duty to 1ms pulse (~3276 u16)
  - Waits 6 seconds for mechanical movement to complete
  - Updates internal state to "CLOSED"
  - Returns after movement complete (blocking)
```

#### Error Responses
```
SERVO:ERROR:empty_command
SERVO:ERROR:invalid_format
SERVO:ERROR:wrong_device:<device_name>
SERVO:ERROR:unknown_command:<cmd>
SERVO:ERROR:command_error:<error_detail>
SERVO:ERROR:buffer_overflow
```

---

## 4. RADAR SENSOR API

### Device Name: `RADAR`
**File Location:** `src/uart_Slave_Radar/main.py`

#### Sensor Simulation Configuration
- **Initial Range:** 123 cm
- **Initial Velocity:** 4.5 m/s
- **Confidence Calculation:** `min(100, max(20, 100 - (range/50)))`
- **Movement Detection:** velocity > 0.5 m/s = 1, else 0

### Commands (UART Protocol)

**PING - Alive Check**
```
Request:  RADAR:PING
Response: RADAR:OK:msg=alive:addr=0x?
```

**WHOAMI - Device Identification**
```
Request:  RADAR:WHOAMI
Response: RADAR:OK:device=RADAR:type=distance_sensor
```

**STATUS - Current Readings**
```
Request:  RADAR:STATUS
Response: RADAR:OK:range=123:velocity=4.5:confidence=75:movement=1

Response fields:
  - range: distance in centimeters (integer)
  - velocity: velocity in m/s (float)
  - confidence: 0-100 percentage (calculated from distance)
  - movement: 1=detected, 0=not detected (based on velocity threshold)
```

**READ - Read Sensor Data**
```
Request:  RADAR:READ
Response: RADAR:OK:range=123:velocity=4.5:confidence=75:movement=1

Same format as STATUS command
```

#### Error Responses
```
RADAR:ERROR:empty_command
RADAR:ERROR:invalid_format
RADAR:ERROR:wrong_device:<device_name>
RADAR:ERROR:unknown_command:<cmd>
RADAR:ERROR:command_error:<error_detail>
RADAR:ERROR:buffer_overflow
```

---

## 5. RESPONSE FORMAT SPECIFICATION

### Response Structure
All responses follow this hierarchy:

```
DEVICE:STATUS[:KEY=VALUE:KEY=VALUE:...]
```

### Response Status Indicators
- **SUCCESS:** `OK` - Command executed successfully
- **ERROR:** `ERROR` - Command failed

### Data Value Encoding
- **Colons (`:`)** separate fields
- **Equals (`=`)** separates key-value pairs
- **Values:** plaintext decimals or strings (no JSON encoding in UART protocol)

### Response Parsing Algorithm
```python
parts = response.split(":", 2)  # Split on first 2 colons only
device = parts[0]              # STEPPER, SERVO, or RADAR
status_section = parts[1]      # OK or ERROR
data_section = parts[2] if len(parts) > 2 else ""  # KEY=VAL:KEY=VAL...

# Parse data key-value pairs
if data_section:
    pairs = data_section.split(":")
    for pair in pairs:
        key, value = pair.split("=", 1)
        data[key] = value
```

---

## 6. ERROR HANDLING PATTERNS

### Command Processing Error Handling

**Level 1: Format Validation**
```
ERROR:empty_command         - No command text received
ERROR:invalid_format        - Malformed request (missing device/cmd)
ERROR:wrong_device:<name>   - Device prefix doesn't match slave
```

**Level 2: Device Communication**
```
ERROR:command_error:<detail>  - Slave command processing failed
ERROR:buffer_overflow         - Receive buffer exceeded 256 bytes
```

**Level 3: Parameter Validation**
```
STEPPER:ERROR:speed_required           - SPIN missing speed arg
STEPPER:ERROR:invalid_speed            - Speed not parseable as int
STEPPER:ERROR:speed_out_of_range       - Speed outside 500-10000µs
STEPPER:ERROR:angle_required           - MOVE missing angle arg
STEPPER:ERROR:invalid_angle            - Angle not parseable
STEPPER:ERROR:delta_required           - ROTATE missing delta arg
STEPPER:ERROR:invalid_delta            - Delta not parseable
```

**Level 4: State Errors**
```
STEPPER:ERROR:not_calibrated  - HOME command required before MOVE/ROTATE
STEPPER:ERROR:home_not_found  - Sensor never triggered during HOME
STEPPER:ERROR:not_rotating    - STOP called but no rotation active
STEPPER:ERROR:move_failed     - MOVE operation failed internally
STEPPER:ERROR:rotate_failed   - ROTATE operation failed internally
```

**Level 5: Unknown Command**
```
ERROR:unknown_command:<cmd>
```

### Master Pico Response Parsing
```python
def parse_device_response(response_str, device):
    """
    Parses: DEVICE:STATUS[:DATA]
    Returns dict with:
      - s: "ok" or "error"
      - msg: status_section string
      - raw: original response
    """
    if not response_str.startswith(f"{device}:"):
        return {"s": "error", "msg": f"wrong_device"}
    
    if "OK" in response_str.upper():
        return {"s": "ok", "msg": response_str, "raw": response_str}
    elif "ERROR" in response_str.upper():
        return {"s": "error", "msg": response_str, "raw": response_str}
    else:
        return {"s": "ok", "msg": response_str, "raw": response_str}
```

### Communication Timeouts
```
SERVO:  8000ms (long movement wait)
STEPPER: 5000ms (normal operations)
RADAR:  2000ms (sensor reads)
```

---

## 7. COMPLETE COMMAND REFERENCE TABLE

### STEPPER Commands

| Command | Arguments | Response | Requires Calib? |
|---------|-----------|----------|-----------------|
| PING | none | `OK:msg=alive:uptime=XXs` | No |
| WHOAMI | none | `OK:device=STEPPER:type=motor_controller` | No |
| STATUS | none | `OK:state=HOME\|ROTATING\|IDLE:position=X:calibrated=1\|0` | No |
| HOME | none | `OK:msg=home_found:pos=0:calib=1` | No |
| MOVE | angle | `OK:msg=moved:pos=X:target=X` | **YES** |
| ROTATE | delta | `OK:msg=rotated:pos=X:delta=X` | **YES** |
| SPIN | speed_us | `OK:msg=spin_started:speed=X:direction=CW` | No |
| STOP | none | `OK:msg=stopped:pos=X:revolutions=Y` | No |
| SPEED | [speed_us] | `OK:msg=current_speed:speed=X` (GET) or `OK:msg=speed_set:speed=X` (SET) | No |
| ENABLE | none | `OK:msg=enabled:enabled=1` | No |
| DISABLE | none | `OK:msg=disabled:enabled=0` | No |

### SERVO Commands

| Command | Arguments | Response |
|---------|-----------|----------|
| PING | none | `OK:msg=alive:uptime=XXs` |
| WHOAMI | none | `OK:device=SERVO:type=actuator` |
| STATUS | none | `OK:state=open\|closed:device=servo` |
| OPEN | none | `OK:msg=opened:state=open` (6s wait) |
| CLOSE | none | `OK:msg=closed:state=closed` (6s wait) |

### RADAR Commands

| Command | Arguments | Response |
|---------|-----------|----------|
| PING | none | `OK:msg=alive:addr=0x?` |
| WHOAMI | none | `OK:device=RADAR:type=distance_sensor` |
| STATUS | none | `OK:range=X:velocity=X.X:confidence=X:movement=0\|1` |
| READ | none | `OK:range=X:velocity=X.X:confidence=X:movement=0\|1` |

---

## 8. IMPLEMENTATION NOTES

### UART Configuration
- **Baud Rate:** 115200
- **Shared Bus:** UART1 (TX=GPIO4, RX=GPIO5)
- **Buffer Size:** 256 bytes per slave
- **Terminator:** `\n` (newline) character
- **Encoding:** UTF-8 ASCII

### Device Identification
- **Device prefix is CASE-INSENSITIVE** in master routing but stored uppercase
- **Commands are CASE-INSENSITIVE** (converted to uppercase before processing)
- **Response format ALWAYS includes device name twice:** once at start, once in error payload

### Position Tracking
- **STEPPER position:** Updated in real-time during movements
- **Range:** 0-360 degrees (normalized on wrap-around)
- **Calibration:** HOME command sets position to exactly 0°
- **Tracking method:** Counts pulses from home position (software position)

### Safety Features
- **Buffer overflow protection:** Max 256 bytes per command
- **Timeout protection:** Master enforces per-device timeout
- **Direction validation:** CW/CCW only (case-insensitive)
- **Speed limits:** Enforced on both MIN (500µs) and MAX (10000µs)

### Master-to-Slave Request-Response Architecture
```
1. Master flushes UART1 buffer
2. Master sends: DEVICE:COMMAND\n
3. Master waits for: DEVICE:STATUS[:DATA]\n (timeout based on device)
4. Master parses response and returns to server
```

