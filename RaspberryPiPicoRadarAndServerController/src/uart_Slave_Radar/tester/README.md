# uart_Slave_Radar - Tester Folder

## UART Radar Slave - Sensor Test

This folder contains test utilities for the UART radar module running on Raspberry Pi Pico.

### Test Files

**`test_radar_sensor.py`** - Interactive test script for radar sensor readings
- Sends commands to radar and displays responses
- Shows simulated distance, velocity, confidence, movement
- Runs automatic test sequence to verify operation
- Allows interactive command testing

### UART Protocol

The radar uses device-addressed UART commands on the shared bus:

**Request Format:**
```
RADAR:COMMAND[:ARGS]\n
```

**Response Format:**
```
RADAR:STATUS[:KEY=VALUE:KEY=VALUE]\n
```

### UART Configuration
- **UART Port:** UART(1)
- **TX Pin:** GPIO 4
- **RX Pin:** GPIO 5
- **Baud Rate:** 115200
- **Data Format:** Text protocol with key=value pairs

### Available Commands

| Command | Args | Response | Purpose |
|---------|------|----------|---------|
| `PING` | None | `RADAR:OK:msg=alive:addr=0x20` | Check if radar is alive |
| `WHOAMI` | None | `RADAR:OK:device=RADAR:type=distance_sensor` | Get device info |
| `READ` | None | `RADAR:OK:range=123:velocity=4.5:confidence=80:movement=1` | Get current sensor readings |
| `STATUS` | None | Same as READ | Get detailed status |
| `SET_RANGE` | `<cm>` | `RADAR:OK:range_set:value=250` | Set distance reading (cm) |
| `SET_VELOCITY` | `<m/s>` | `RADAR:OK:velocity_set:value=8.5` | Set velocity reading (m/s) |

### Example Command Sequences

**Check if radar is online:**
```
>>> RADAR:PING
<<< RADAR:OK:msg=alive:addr=0x20
```

**Get current sensor reading:**
```
>>> RADAR:READ
<<< RADAR:OK:range=250:velocity=8.5:confidence=80:movement=1
```

**Simulate new distance (300cm):**
```
>>> RADAR:SET_RANGE:300
<<< RADAR:OK:range_set:value=300
```

**Simulate new velocity (6.2 m/s):**
```
>>> RADAR:SET_VELOCITY:6.2
<<< RADAR:OK:velocity_set:value=6.2
```

### How to Use the Test Script

1. **Load the test script on your Pico:**
   - Open `test_radar_sensor.py` in your MicroPython IDE
   - Make sure the main radar firmware (`main.py`) is also running
   - Upload and run the test script

2. **View the output:**
   - The script sends 7 test commands automatically
   - Watch the output for each command and response
   - Verify all readings are printed correctly

3. **Example output:**
   ```
   [TEST 1] PING - Check if radar is alive
   >>> Sending: RADAR:PING
   <<< Response: RADAR:OK:msg=alive:addr=0x20
   
   ============================================================
   RADAR SENSOR STATUS
   ============================================================
     Message:      alive
     Address:      0x20
   ============================================================
   
   [TEST 2] WHOAMI - Identify device
   >>> Sending: RADAR:WHOAMI
   <<< Response: RADAR:OK:device=RADAR:type=distance_sensor
   ```

### Response Field Reference

| Field | Example | Meaning |
|-------|---------|---------|
| `range` | `range=250` | Distance reading: 250 cm (2.5 meters) |
| `velocity` | `velocity=8.5` | Speed: 8.5 m/s |
| `confidence` | `confidence=80` | Signal confidence: 80% |
| `movement` | `movement=1` | Movement detected: Yes (1=yes, 0=no) |
| `addr` | `addr=0x20` | Device address on UART bus |
| `device` | `device=RADAR` | Device identifier |
| `type` | `type=distance_sensor` | Sensor type |

### Integration with Node.js Server

After testing with this script:

1. Start the Node.js server on Raspberry Pi:
   ```bash
   npm run server:start
   ```

2. Open the web dashboard:
   ```
   http://raspberrypi.local:3000
   ```

3. Go to the Radar Control view - you should see:
   - Live distance readings
   - Velocity measurements
   - Confidence levels
   - Movement detection status

### Troubleshooting

**No response from radar:**
- Verify UART cable connections
- Check that main radar firmware is running
- Ensure baud rate is 115200

**Garbled output:**
- Check for loose connections
- Try moving UART cables away from power cables
- Reduce cable length if possible

**Confidence always shows 0:**
- This is normal if range is 0
- Try `SET_RANGE:200` to simulate a distance reading
