# Radar Project API Documentation

## Overview

Complete API reference for the RadarProject full-stack application. The system uses a hierarchical command routing architecture:

**Client (Vue 3) → Server API (Express.js) → Pico Master (UART) → Slave Devices (Pico Controllers)**

---

## Command Format

All device commands follow the format:

```
DEVICE:COMMAND[:ARGS]
```

### Examples
- Read-only: `STEPPER:STATUS`
- With positional args: `STEPPER:MOVE:360`
- With named args: `RADAR:SET_RANGE:centimeters=100` (supported for compatibility)

---

## Device Commands

### STEPPER (Stepper Motor Controller - I2C 0x10)

| Command | Args | Example | Timeout | Description |
|---------|------|---------|---------|-------------|
| PING | none | `STEPPER:PING` | 2s | Alive check |
| WHOAMI | none | `STEPPER:WHOAMI` | 2s | Device identification |
| STATUS | none | `STEPPER:STATUS` | 2s | Get full status (position, enabled, calibrated, at_home) |
| ENABLE | none | `STEPPER:ENABLE` | 2s | Enable motor (power on) |
| DISABLE | none | `STEPPER:DISABLE` | 2s | Disable motor (power off) |
| HOME | none | `STEPPER:HOME` | 5s | Find and calibrate home position (0°) |
| MOVE | degrees (0-360) | `STEPPER:MOVE:360` | 5s | Absolute position move |
| ROTATE | delta_degrees (±X) | `STEPPER:ROTATE:45` | 3s | Relative rotation |
| SPIN | speed_us (500-10000) | `STEPPER:SPIN:2000` | 2s | Continuous rotation at speed |
| STOP | none | `STEPPER:STOP` | 2s | Stop any motion |
| SPEED | speed_us (500-10000) | `STEPPER:SPEED:2000` | 2s | Set motor speed |

**Special Values:**
- `MOVE:360` = Raise to maximum (used by UI raise button)
- `MOVE:0` = Lower to minimum (used by UI lower button)

---

### SERVO / ACTUATOR (Linear Servo Controller - I2C 0x12)

| Command | Args | Example | Timeout | Description |
|---------|------|---------|---------|-------------|
| PING | none | `SERVO:PING` | 2s | Alive check |
| WHOAMI | none | `SERVO:WHOAMI` | 2s | Device identification |
| STATUS | none | `SERVO:STATUS` | 2s | Get current state (open/closed) |
| OPEN | none | `SERVO:OPEN` | 8s | Extend/open actuator |
| CLOSE | none | `SERVO:CLOSE` | 8s | Retract/close actuator |

**Coordination:**
- Raise button triggers: `STEPPER:MOVE:360` + `SERVO:OPEN` (sequentially)
- Lower button triggers: `STEPPER:MOVE:0` + `SERVO:CLOSE` (sequentially)

---

### RADAR (Radar Sensor - UART continuous stream)

| Command | Args | Example | Timeout | Description |
|---------|------|---------|---------|-------------|
| PING | none | `RADAR:PING` | 2s | Alive check |
| WHOAMI | none | `RADAR:WHOAMI` | 2s | Device identification |
| STATUS | none | `RADAR:STATUS` | 2s | Get radar status |
| READ | none | `RADAR:READ` | 2s | Get current sensor readings |
| SET_RANGE | centimeters (0-500) | `RADAR:SET_RANGE:100` | 2s | Simulate/set range (testing) |
| SET_VELOCITY | m/s (0.0-50.0) | `RADAR:SET_VELOCITY:5.0` | 2s | Simulate/set velocity (testing) |

**Response Format:**
```json
{
  "s": "ok",
  "pos": 45.0,
  "range": 250,
  "velocity": 5.5,
  "confidence": 85,
  "movement": 1
}
```

---

## Client API Endpoints

### REST API

All endpoints POST to `/api/device/:device/:command`

#### Request Format
```javascript
POST /api/device/STEPPER/MOVE
Content-Type: application/json

{
  "args": {
    "degrees": 360
  }
}
```

#### Response Format
```javascript
{
  "success": true,
  "command": "STEPPER:MOVE:360",
  "response": {
    "s": "ok",
    "device": "STEPPER",
    "data": {
      "position": 360,
      "motorState": "idle"
    }
  }
}
```

### WebSocket Events (Socket.IO)

System broadcasts `system:status` every 5 seconds:
```javascript
{
  "stepper": { "position": 180, "enabled": 1 },
  "servo": { "state": "open" },
  "radar": { "range": 250, "movement": 1 },
  "timestamp": 1713049200000
}
```

---

## Vuex Store Dispatch Commands

### Stepper Module (`store/modules/stepper.js`)
```javascript
dispatch('stepper/moveToAngle', { angle: 360, speed: 50 })
dispatch('stepper/raise')    // Moves to 360°
dispatch('stepper/lower')    // Moves to 0°
dispatch('stepper/stop')
dispatch('stepper/enable')
dispatch('stepper/disable')
dispatch('stepper/homePosition')
dispatch('stepper/fetchStatus')
```

### Actuator Module (`store/modules/actuator.js`)
```javascript
dispatch('actuator/open')    // Extends servo
dispatch('actuator/close')   // Retracts servo
dispatch('actuator/fetchStatus')
```

### Radar Module (`store/modules/radar.js`)
```javascript
dispatch('radar/updateSweepAngle', angle)  // Update real-time sweep display
```

---

## Vue Component Examples

### Stepper Control View
```vue
<template>
  <button @click="raiseMotor" :disabled="!canRaise">
    ⬆️ Raise {{ isFullyRaised ? '(MAX)' : '' }}
  </button>
  <button @click="lowerMotor" :disabled="!canLower">
    ⬇️ Lower {{ isFullyLowered ? '(MIN)' : '' }}
  </button>
</template>

<script>
export default {
  methods: {
    async raiseMotor() {
      await this.raise()      // STEPPER:MOVE:360
      await this.open()       // SERVO:OPEN
    },
    async lowerMotor() {
      await this.lower()      // STEPPER:MOVE:0
      await this.close()      // SERVO:CLOSE
    }
  }
}
</script>
```

---

## Pico Master Routing

The Pico Master acts as a flexible pass-through, accepting:
- **Positional arguments** (preferred): `STEPPER:MOVE:360`
- **Named arguments** (compatibility): `STEPPER:MOVE:degrees=360`

The Master automatically:
1. Validates device existence
2. Forwards command to correct slave
3. Parses and reformats response
4. Returns JSON to server

---

## Testing

Run comprehensive API test suite:
```bash
cd ~/RadarProject/RadarApp-Microcontroller/src/UART_Master_API/tester
python3 comprehensive_api_test.py
```

This validates:
- ✓ All STEPPER commands
- ✓ All SERVO commands
- ✓ All RADAR commands
- ✓ Command formatting
- ✓ Response parsing
- ✓ Timeout handling
- ✓ Error recovery

---

## Error Handling

### Standard Error Response
```json
{
  "s": "error",
  "msg": "unknown_command",
  "device": "STEPPER",
  "status": "ERROR"
}
```

### Timeout Behavior
- Clients wait 10 seconds for response
- Server can retry with backoff
- Failed commands trigger error notifications
- Hardware can remain operational while single commands fail

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| PING | 100-500ms | Roundtrip test |
| STATUS | 200-600ms | Read sensor data |
| MOVE:360 | 5-10s | Full travel time |
| SERVO:OPEN | 6-8s | Full extension |
| SERVO:CLOSE | 6-8s | Full retraction |

---

## Troubleshooting

### Commands Timing Out
1. Check Pico connection: `STEPPER:PING`
2. Verify UART at 460800 baud
3. Check for I2C slave response: Try sending ping directly

### Wrong Parameter Format
- Client sends: `{ args: { degrees: 360 } }`
- Server formats: `STEPPER:MOVE:360` ✓
- NOT: `STEPPER:MOVE:degrees=360` (wrong)

### Coordination Issues (Raise/Lower)
- Must await each operation sequentially
- If stepper MOVE times out, servo won't get OPEN/CLOSE command
- Use async/await to ensure proper ordering

---

## Version

- **API Version**: 1.0
- **Last Updated**: April 13, 2026
- **Pico Master**: Pass-through router v1.0
- **Slave Firmware**: Compatible with UART_Slave_* v1.0
