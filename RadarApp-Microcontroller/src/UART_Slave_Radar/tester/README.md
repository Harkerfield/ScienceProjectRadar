# uart_Slave_Radar - Tester Folder

## UART Radar Slave - Sensor Test

This folder contains test utilities for the UART radar module running on Raspberry Pi Pico.

### Test Files

**`test_radar_sensor.py`** - UART Protocol Test
- Tests the UART slave commands interface
- Sends device commands and displays responses
- Simulates distance, velocity, confidence, movement
- Runs automatic test sequence to verify operation
- **Purpose:** Verify UART communication working

**`test_hb100_if_only.py`** - Raw IF Signal Tester
- Direct ADC reading of HB100 IF (Intermediate Frequency) output
- Flexible GPIO pin configuration (any ADC-capable pin)
- Tests raw signal analysis and Doppler frequency estimation
- **Use when:** Testing raw HB100 sensor wired directly to Pico
- **Features:**
  - Single sample reading
  - Continuous monitoring
  - Raw ADC CSV stream for analysis
  - Motion intensity estimation
  - Frequency detection test

**`test_hb100_cqrobot.py`** - CQRobot Module Tester
- Tests pre-built CQRobot HB100 module (SKU: CQRSENWB01)
- Dual-sensor reading: Analog IF + Digital motion detection pin
- Optimized for CQRobot standard pinout
- **Use when:** Testing CQRobot module with motion pin support
- **Features:**
  - Dual IF + motion pin monitoring
  - Motion pin impulse detection
  - Sensitivity threshold testing
  - IF vs motion pin correlation analysis
  - Combined intensity calculation

**`test_raw_uart_data.py`** - Raw UART Data Debugger
- Real-time monitoring of raw UART bus data
- Capture and analyze bytes in hex/ASCII format
- Debug protocol communication issues
- **Use when:** Troubleshooting UART communication or protocol problems
- **Features:**
  - Continuous hex monitor with real-time display
  - Line-by-line message capture (newline-delimited)
  - Single or timed data capture
  - Send raw commands and view responses
  - Hex dump of buffer contents
  - ping all devices for quick connectivity test
  - Statistics and buffer management

### Which Test to Use?

| Scenario | Use This | Reason |
|----------|----------|--------|
| **Sensor testing** | | |
| Testing raw HB100 sensor wired to GPIO | `test_hb100_if_only.py` | Direct ADC, flexible pins |
| Testing CQRobot module with motion pin | `test_hb100_cqrobot.py` | Dual IF + motion detection |
| Analyzing raw IF signal | `test_hb100_if_only.py` | CSV stream for analysis |
| **UART Debugging** | | |
| UART communication not working | `test_raw_uart_data.py` | See actual bytes on wire |
| Device not responding to commands | `test_raw_uart_data.py` | Verify messages being sent |
| Garbled or corrupted data | `test_raw_uart_data.py` | Inspect hex dump |
| Protocol issues or misalignment | `test_raw_uart_data.py` | Monitor real-time traffic |
| Quick connectivity test | `test_raw_uart_data.py` | Send pings to all devices |
| **Protocol Testing** | | |
| UART slave protocol test | `test_radar_sensor.py` | Test command/response protocol |

### UART Protocol

The radar uses device-addressed UART commands on the shared bus:

**Request Format:**
```
RADAR:COMMAND[:ARGS]\n
```

**Response Format:**
```
RADAR:status[:KEY=VALUE:KEY=VALUE]\n
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
| `ping` | None | `RADAR:OK:msg=alive:addr=0x20` | Check if radar is alive |
| `whoami` | None | `RADAR:OK:device=RADAR:type=distance_sensor` | Get device info |
| `read` | None | `RADAR:OK:range=123:velocity=4.5:confidence=80:movement=1` | Get current sensor readings |
| `status` | None | Same as read | Get detailed status |
| `set_range` | `<cm>` | `RADAR:OK:range_set:value=250` | Set distance reading (cm) |
| `set_velocity` | `<m/s>` | `RADAR:OK:velocity_set:value=8.5` | Set velocity reading (m/s) |

### Example Command Sequences

**Check if radar is online:**
```
>>> RADAR:ping
<<< RADAR:OK:msg=alive:addr=0x20
```

**Get current sensor reading:**
```
>>> RADAR:read
<<< RADAR:OK:range=250:velocity=8.5:confidence=80:movement=1
```

**Simulate new distance (300cm):**
```
>>> RADAR:set_range:300
<<< RADAR:OK:range_set:value=300
```

**Simulate new velocity (6.2 m/s):**
```
>>> RADAR:set_velocity:6.2
<<< RADAR:OK:velocity_set:value=6.2
```

### How to Use the Test Script

#### test_radar_sensor.py (UART Protocol Test)

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
   [TEST 1] ping - Check if radar is alive
   >>> Sending: RADAR:ping
   <<< Response: RADAR:OK:msg=alive:addr=0x20
   
   ============================================================
   RADAR SENSOR status
   ============================================================
     Message:      alive
     Address:      0x20
   ============================================================
   
   [TEST 2] whoami - Identify device
   >>> Sending: RADAR:whoami
   <<< Response: RADAR:OK:device=RADAR:type=distance_sensor
   ```

#### test_hb100_if_only.py (Raw IF Signal Test)

1. **Wiring:**
   - Connect HB100 IF output to GPIO27 (or modify `IF_PIN`)
   - Connect HB100 VCC to 3.3V
   - Connect HB100 GND to GND

2. **Run the test:**
   - Upload and run `test_hb100_if_only.py` on Pico
   - You'll see an interactive menu with 7 options
   - Choose test mode (single sample, continuous, etc.)

3. **Menu options:**
   - Single Sample: Read 5 sensor readings
   - Continuous Monitor: 30-second monitoring
   - Infinite Monitor: Monitor until Ctrl+C
   - Raw ADC Stream: CSV output for spreadsheet analysis
   - Sensitivity Test: Calibrate motion threshold
   - Frequency Test: Estimate Doppler frequency

#### test_hb100_cqrobot.py (CQRobot Module Test)

1. **Wiring:**
   - CQRobot IF Output → GPIO27 (ADC1)
   - CQRobot Motion Pin → GPIO26 (Digital)
   - CQRobot VCC → 3.3V
   - CQRobot GND → GND

2. **Run the test:**
   - Upload and run `test_hb100_cqrobot.py` on Pico
   - Interactive menu with 8 options
   - Tests both IF and motion pin

3. **Menu options:**
   - Single Sample: Read both sensors
   - Dual Monitor: 30-second dual monitoring
   - Infinite Dual Monitor: Continuous monitoring
   - Motion Pin Test: Digital pin detection only
   - IF Stream: Analog signal only (CSV)
   - Sensitivity Test: Motion pin response thresholds
   - Correlation Test: IF vs pin agreement analysis

#### test_raw_uart_data.py (Raw UART Data Debugger)

1. **Setup:**
   - No special wiring needed (connects to main UART bus)
   - Run alongside main firmware for live monitoring
   - Must have other devices on the bus for meaningful data

2. **Run the test:**
   - Upload and run `test_raw_uart_data.py` on Pico
   - Monitors incoming/outgoing UART data
   - Interactive menu with 10 options

3. **Menu options:**
   - **1. Continuous Hex Monitor** - Live hex display of incoming data
   - **2. Line-by-Line Monitor** - Captures complete messages (newline-delimited)
   - **3. Single Capture** - Waits for one message with 5s timeout
   - **4. Timed Capture** - Record data for N seconds to CSV
   - **5. Send Raw Command** - Send hex or text commands (e.g., `RADAR:ping\n`)
   - **6. Stats & Buffer Info** - Show RX/TX bytes and current buffer
   - **7. Raw Hex Dump** - Display all buffered data as hex dump
   - **8. Clear Buffer** - Clear receive buffer
   - **9. Test Devices** - Send ping to all devices (stepper, servo, RADAR)
   - **A. Exit** - Exit test

4. **Usage examples:**

   **Verify UART is working:**
   ```
   Select: 9 (Test Devices)
   → Sends ping to all devices
   → Shows responses in hex and ASCII
   ```

   **Capture protocol exchange:**
   ```
   Select: 4 (Timed Capture)
   Enter duration: 20
   → Captures 20 seconds of traffic
   → Shows hex dump of all data
   ```

   **Debug garbled messages:**
   ```
   Select: 2 (Line-by-Line Monitor)
   → Captures each newline-delimited message
   → Shows hex and ASCII for each
   → Can spot encoding issues
   ```

   **Send custom command:**
   ```
   Select: 5 (Send Raw Command)
   Enter: RADAR:set_range:300
   → Sends command on UART
   → Can then use menu option 2 to see response
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

#### test_radar_sensor.py Issues

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
- Try `set_range:200` to simulate a distance reading

#### test_hb100_if_only.py Issues

**No ADC readings (always 0):**
- Check IF output is connected to GPIO27 (or your configured ADC pin)
- Verify power is connected to sensor
- Move sensor away from metal objects
- Check GPIO pin is ADC-capable (GPIO26-29)

**Readings don't change:**
- Sensor might be stationary (readings are stable until motion)
- Wave hand over sensor to see variation
- Check IF output isn't floating (should have baseline ~30000-50000)

**Motion intensity always 0:**
- Increase motion threshold in code
- Check signal baseline with raw ADC stream
- Ensure sensor has power and IF connection

#### test_hb100_cqrobot.py Issues

**Motion pin always 0:**
- Check GPIO26 is connected to CQRobot MOTION pin
- Verify CQRobot has power
- Wave hand directly over sensor
- Try sensitivity test to check threshold

**IF readings but motion pin stuck:**
- Motion pin might be configured incorrectly
- Check cable connection to GPIO26
- Verify Pin 26 isn't used elsewhere

**Both readings stuck:**
- Check both GPIO connections
- Verify power to CQRobot module
- Remove and re-seat module

#### test_raw_uart_data.py Issues

**No data received:**
- Verify main firmware (main.py) is running
- Check UART TX/RX cables are connected
- Baud rate should be 115200
- Try sending commands (menu option 5) first, then monitor

**Only see sent data, no responses:**
- Devices might not be powered on
- Check device addresses: stepper=0x10, servo=0x11, RADAR=0x20
- Try "Test Devices" (menu 9) to verify connectivity
- Check for UART bus contention

**Garbled or incomplete messages:**
- Some bytes might be lost due to timing
- Try slower capture (menu 4 with longer duration)
- Check cable quality and length
- Move cables away from power lines

**Buffer fills up too fast:**
- Use menu 8 to clear buffer periodically
- Reduce monitoring duration
- Check for runaway messages (device stuck sending garbage)

**Commands sent but no response:**
- Device might not recognize address format
- Try menu option 2 (line-by-line) to see what's actually being received
- Verify protocol format: `DEVICE:COMMAND\n`
- Check device firmware is correct

### Additional Resources

See **[HB100_SETUP.md](./HB100_SETUP.md)** for:
- Detailed hardware setup guides
- Pinout diagrams for standalone vs CQRobot
- Troubleshooting hardware issues
- Integration with main.py
