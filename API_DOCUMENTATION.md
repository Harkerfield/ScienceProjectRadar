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
- Read-only: `stepper:status`
- With positional args: `stepper:move:360`
- With named args: `radar:set_range:centimeters=100` (supported for compatibility)

---

## Device Commands

### stepper (Stepper Motor Controller - I2C 0x10)

| Command | Args | Example | Timeout | Description |
|---------|------|---------|---------|-------------|
| ping | none | `stepper:ping` | 2s | Alive check |
| whoami | none | `stepper:whoami` | 2s | Device identification |
| status | none | `stepper:status` | 2s | Get full status (position, enabled, calibrated, at_home) |
| enable | none | `stepper:enable` | 2s | Enable motor (power on) |
| disable | none | `stepper:disable` | 2s | Disable motor (power off) |
| home | none | `stepper:home` | 5s | Find and calibrate home position (0°) |
| move | degrees (0-360) | `stepper:move:360` | 5s | Absolute position move |
| rotate | delta_degrees (±X) | `stepper:rotate:45` | 3s | Relative rotation |
| spin | speed_us (500-10000) | `stepper:spin:2000` | 2s | Continuous rotation at speed |
| stop | none | `stepper:stop` | 2s | Stop any motion |
| speed | speed_us (500-10000) | `stepper:speed:2000` | 2s | Set motor speed |

**Special Values:**
- `move:360` = Raise to maximum (used by UI raise button)
- `move:0` = Lower to minimum (used by UI lower button)

---

### servo / servo (Linear Servo Controller - I2C 0x12)

| Command | Args | Example | Timeout | Description |
|---------|------|---------|---------|-------------|
| ping | none | `servo:ping` | 2s | Alive check |
| whoami | none | `servo:whoami` | 2s | Device identification |
| status | none | `servo:status` | 2s | Get current state (open/closed) |
| open | none | `servo:open` | 8s | Extend/open actuator |
| close | none | `servo:close` | 8s | Retract/close actuator |

**Coordination:**
- Raise button triggers: `stepper:move:360` + `servo:open` (sequentially)
- Lower button triggers: `stepper:move:0` + `servo:close` (sequentially)

---

### radar (Radar Sensor - UART continuous stream)

| Command | Args | Example | Timeout | Description |
|---------|------|---------|---------|-------------|
| ping | none | `radar:ping` | 2s | Alive check |
| whoami | none | `radar:whoami` | 2s | Device identification |
| status | none | `radar:status` | 2s | Get radar status |
| read | none | `radar:read` | 2s | Get current sensor readings |
| set_range | centimeters (0-500) | `radar:set_range:100` | 2s | Simulate/set range (testing) |
| set_velocity | m/s (0.0-50.0) | `radar:set_velocity:5.0` | 2s | Simulate/set velocity (testing) |

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
POST /api/device/stepper/move
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
  "command": "stepper:move:360",
  "response": {
    "s": "ok",
    "device": "stepper",
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
      await this.raise()      // stepper:move:360
      await this.open()       // servo:open
    },
    async lowerMotor() {
      await this.lower()      // stepper:move:0
      await this.close()      // servo:close
    }
  }
}
</script>
```

---

## Pico Master Routing

The Pico Master acts as a flexible pass-through, accepting:
- **Positional arguments** (preferred): `stepper:move:360`
- **Named arguments** (compatibility): `stepper:move:degrees=360`

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
- ✓ All stepper commands
- ✓ All servo commands
- ✓ All radar commands
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
  "device": "stepper",
  "status": "error"
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
| ping | 100-500ms | Roundtrip test |
| status | 200-600ms | Read sensor data |
| move:360 | 5-10s | Full travel time |
| servo:open | 6-8s | Full extension |
| servo:close | 6-8s | Full retraction |

---

## Troubleshooting

### Commands Timing Out
1. Check Pico connection: `stepper:ping`
2. Verify UART at 460800 baud
3. Check for I2C slave response: Try sending ping directly

### Wrong Parameter Format
- Client sends: `{ args: { degrees: 360 } }`
- Server formats: `stepper:move:360` ✓
- NOT: `stepper:move:degrees=360` (wrong)

### Coordination Issues (Raise/Lower)
- Must await each operation sequentially
- If stepper move times out, servo won't get open/close command
- Use async/await to ensure proper ordering

---

## Version

- **API Version**: 1.0
- **Last Updated**: April 13, 2026
- **Pico Master**: Pass-through router v1.0
- **Slave Firmware**: Compatible with UART_Slave_* v1.0
