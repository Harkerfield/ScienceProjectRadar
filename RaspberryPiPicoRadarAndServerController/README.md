
# Raspberry Pi Pico Radar and Server Controller (I2C Master/Slave + UART Architecture)

This project implements a modular radar and actuator system using multiple Raspberry Pi Picos communicating over I2C and UART. The master Pico acts as an I2C master for stepper/actuator slaves while reading radar data via UART from the radar Pico. All Picos support USB serial for interactive testing and debugging.

**All slave responses use standardized JSON format:** `{"s":"ok",...}` or `{"s":"error","msg":"..."}`


## Hardware Architecture

- 1x **Master Pico** (I2C master, UART/USB to server, reads radar via UART1)
- 1x **Stepper Pico** (I2C slave @ 0x10, controls stepper motor)
- 1x **Actuator Pico** (I2C slave @ 0x12, controls servo/actuator)
- 1x **Radar Pico** (UART slave via UART1, transmits radar data continuously)
- Radar modules (RCWL-0516 or CQRobot)
- RC Servo Motor (for landing gear)



## Communication Architecture

**Dual Bus System:**
- **I2C Bus (SDA/SCL):** Master Pico ↔ Stepper Pico (0x10), Actuator Pico (0x12)
- **UART Bus (TX1/RX1):** Master Pico ↔ Radar Pico (continuous data stream)
- **USB Serial:** All Picos support REPL for interactive testing and debugging

---

## Slave Commands Reference

### Stepper Motor (I2C @ 0x10)
All responses in JSON format: `{"s":"ok","key":value}`

| Command | Response | Purpose |
|---------|----------|---------|
| `FIND_HOME` | `{"s":"ok","pos":0,"calib":1}` | Calibrate home position |
| `MOVE:<angle>` | `{"s":"ok","pos":90.0}` | Move to absolute angle (degrees) |
| `ROTATE:<degrees>` | `{"s":"ok","pos":45.0}` | Rotate by relative amount |
| `START_ROTATE:CW\|CCW` | `{"s":"ok","msg":"rotating","dir":"CW"}` | Start continuous rotation |
| `STOP_ROTATE` | `{"s":"ok","pos":90.0,"rev":1}` | Stop continuous rotation |
| `SPEED:<microseconds>` | `{"s":"ok","speed":2000}` | Set pulse speed (500-10000µs) |
| `STATUS` | `{"s":"ok","pos":45.0,"home":0,...}` | Full system status |
| `POSITION` | `{"s":"ok","pos":45.0,"rev":1,"total":405.0}` | Current position & revolutions |
| `PING` | `{"s":"ok","msg":"alive","addr":"0x10"}` | Verify online |

**Pin Configuration:**
- GPIO 5: Pulse (PUL)
- GPIO 6: Direction (DIR)
- GPIO 7: Enable (ENA)
- GPIO 8-10: Microstepping (MS1-3)
- GPIO 20: Home Sensor

**Motor:** NEMA17 + 3:1 gear reduction = 600 steps/revolution (0.6°/step)  
**Default Speed:** 2000µs (slow, good holding torque)

---

### Actuator / Landing Gear (I2C @ 0x12)
All responses in JSON format: `{"s":"ok","key":value}`

| Command | Response | Purpose |
|---------|----------|---------|
| `OPEN` | `{"s":"ok","msg":"opened","pos":100}` | Extend actuator |
| `CLOSE` | `{"s":"ok","msg":"closed","pos":0}` | Retract actuator |
| `STATUS` | `{"s":"ok","state":"open","pos":100}` | Current state |
| `POSITION` | `{"s":"ok","pos":100}` | Current position (0-100) |
| `PING` | `{"s":"ok","msg":"alive","addr":"0x12"}` | Verify online |

**Pin Configuration:**
- GPIO 2: PWM Signal to RC servo
- 50Hz frequency
- 6553 duty = fully extended
- 3277 duty = fully retracted

**Device:** RC Servo Motor (3-wire: Brown=GND, Red=5V, Yellow=Signal)

---

### Radar Sensor (UART @ 0x20)
All responses in JSON format: `{"s":"ok","range":<cm>,"vel":<m/s>}`

**Continuous Output (every 100ms):** 
```json
{"s":"ok","range":123,"vel":4.5}
```

**USB Commands (for testing/config):**

| Command | Response | Purpose |
|---------|----------|---------|
| `READ` | `{"s":"ok","range":123,"vel":4.5}` | Get current reading |
| `STATUS` | `{"s":"ok","msg":"operational",...}` | System operational check |
| `RANGE:<cm>` | `{"s":"ok","msg":"range_set",...}` | Set range value (testing) |
| `VEL:<m/s>` | `{"s":"ok","msg":"vel_set",...}` | Set velocity value (testing) |
| `PING` | `{"s":"ok","msg":"alive","addr":"0x20"}` | Verify online |
| `HELP` | Command list | Show available commands |

**Pin Configuration:**
- UART1: TX=GPIO4, RX=GPIO5
- Baud: 115200
- Output: Continuous JSON stream

**Sensor:** RCWL-0516 or CQRobot 10.525GHz  
**Range:** 0-400 cm  
**Velocity:** ±20 m/s (Doppler effect)

---

## Slave Commands Reference

### Stepper Motor (I2C @ 0x10)
All responses in JSON format: `{"s":"ok","key":value}`

| Command | Response | Purpose |
|---------|----------|---------|
| `FIND_HOME` | `{"s":"ok","pos":0,"calib":1}` | Calibrate home position |
| `MOVE:<angle>` | `{"s":"ok","pos":90.0}` | Move to absolute angle (degrees) |
| `ROTATE:<degrees>` | `{"s":"ok","pos":45.0}` | Rotate by relative amount |
| `START_ROTATE:CW\|CCW` | `{"s":"ok","msg":"rotating","dir":"CW"}` | Start continuous rotation |
| `STOP_ROTATE` | `{"s":"ok","pos":90.0,"rev":1}` | Stop continuous rotation |
| `SPEED:<microseconds>` | `{"s":"ok","speed":2000}` | Set pulse speed (500-10000µs) |
| `STATUS` | `{"s":"ok","pos":45.0,"home":0,...}` | Full system status |
| `POSITION` | `{"s":"ok","pos":45.0,"rev":1,"total":405.0}` | Current position & revolutions |
| `PING` | `{"s":"ok","msg":"alive","addr":"0x10"}` | Verify online |

**Pin Configuration:**
- GPIO 5: Pulse (PUL)
- GPIO 6: Direction (DIR)
- GPIO 7: Enable (ENA)
- GPIO 8-10: Microstepping (MS1-3)
- GPIO 20: Home Sensor

**Motor:** NEMA17 + 3:1 gear reduction = 600 steps/revolution (0.6°/step)  
**Default Speed:** 2000µs (slow, good holding torque)

---

### Actuator / Landing Gear (I2C @ 0x12)
All responses in JSON format: `{"s":"ok","key":value}`

| Command | Response | Purpose |
|---------|----------|---------|
| `OPEN` | `{"s":"ok","msg":"opened","pos":100}` | Extend actuator |
| `CLOSE` | `{"s":"ok","msg":"closed","pos":0}` | Retract actuator |
| `STATUS` | `{"s":"ok","state":"open","pos":100}` | Current state |
| `POSITION` | `{"s":"ok","pos":100}` | Current position (0-100) |
| `PING` | `{"s":"ok","msg":"alive","addr":"0x12"}` | Verify online |

**Pin Configuration:**
- GPIO 2: PWM Signal to RC servo
- 50Hz frequency
- 6553 duty = fully extended
- 3277 duty = fully retracted

**Device:** RC Servo Motor (3-wire: Brown=GND, Red=5V, Yellow=Signal)

---

### Radar Sensor (UART @ 0x20)
All responses in JSON format: `{"s":"ok","range":<cm>,"vel":<m/s>}`

**Continuous Output (every 100ms):** 
```json
{"s":"ok","range":123,"vel":4.5}
```

**USB Commands (for testing/config):**

| Command | Response | Purpose |
|---------|----------|---------|
| `READ` | `{"s":"ok","range":123,"vel":4.5}` | Get current reading |
| `STATUS` | `{"s":"ok","msg":"operational",...}` | System operational check |
| `RANGE:<cm>` | `{"s":"ok","msg":"range_set",...}` | Set range value (testing) |
| `VEL:<m/s>` | `{"s":"ok","msg":"vel_set",...}` | Set velocity value (testing) |
| `PING` | `{"s":"ok","msg":"alive","addr":"0x20"}` | Verify online |
| `HELP` | Command list | Show available commands |

**Pin Configuration:**
- UART1: TX=GPIO4, RX=GPIO5
- Baud: 115200
- Output: Continuous JSON stream

**Sensor:** RCWL-0516 or CQRobot 10.525GHz  
**Range:** 0-400 cm  
**Velocity:** ±20 m/s (Doppler effect)

---

Assign the 6 wires as follows:
```
1. SDA (I2C Data)      - Connected to Master Pico GP0, all I2C slaves
2. SCL (I2C Clock)     - Connected to Master Pico GP1, all I2C slaves
3. TX (UART Transmit)  - Radar Pico → Master Pico UART1 RX (GP5)
4. RX (UART Receive)   - Master Pico UART1 TX (GP4) → Radar Pico
5. GND (Common Ground) - All Picos
6. 5V (Power)          - All Picos
```

- **I2C Slaves (I2C Bus):** 
  - Stepper Pico @ address 0x10
  - Actuator Pico @ address 0x12
- **UART Slave (UART1 Bus):** 
  - Radar Pico (transmits continuous radar data)
- **Power:** 5V and GND shared by all devices

### Default Pin Assignments
- **Servo Control:** GPIO 16 (PWM)
- **Status LED:** GPIO 25 (built-in LED)
- **UART to Pi4:** GPIO 8 (TX), GPIO 9 (RX)

### RCWL-0516 Option
- **Sensor 1:** GPIO 2
- **Sensor 2:** GPIO 3
- **Sensor 3:** GPIO 4
- **Sensor 4:** GPIO 5
- **Sensor 5:** GPIO 6
- **Sensor 6:** GPIO 7
- **Sensor 7:** GPIO 8
- **Sensor 8:** GPIO 9

### CQRobot 10.525GHz Option
- **Module 1 UART:** UART0 (TX: GPIO 0, RX: GPIO 1)
- **Module 2 UART:** UART1 (TX: GPIO 4, RX: GPIO 5)


## File Structure (Core Files)

```
RaspberryPiPicoRadarAndServerController/
├── main.py                           # Main application entry point
├── PINOUT_AND_CONNECTIONS.md         # Hardware wiring guide
├── src/
│   ├── i2c_Master_API/
│   │   ├── main.py                   # Master Pico I2C/UART controller (USB testable)
│   │   └── README.md                 # Master API documentation
│   ├── i2c_Slave_Stepper/
│   │   ├── main.py                   # Stepper Pico I2C slave firmware
│   │   ├── stepper.py                # Motor control library
│   │   ├── I2C_API.md                # Stepper API documentation
│   │   ├── JSON_API.md               # Detailed JSON responses
│   │   └── tester/
│   │       ├── README.md             # Tester documentation
│   │       └── test_*.py             # Test scripts
│   ├── i2c_Slave_Actuator/
│   │   ├── main.py                   # Actuator Pico I2C slave firmware
│   │   ├── I2C_API.md                # Actuator API documentation
│   │   └── tester/
│   │       ├── README.md             # Tester documentation
│   │       └── test_actuator_control.py
│   └── uart_Slave_Radar/
│       ├── main.py                   # Radar Pico UART slave firmware
│       ├── UART_API.md               # Radar API documentation
│       └── tester/
│           └── README.md             # Tester documentation
├── config/
│   └── settings.py                   # Configuration settings
├── lib/                              # Libraries (if needed)
└── README.md                         # This file
```

**Documentation Files:**
- `JSON_API.md` - Complete JSON API reference for Stepper
- `UART_API.md` - Complete UART API reference for Radar
- `SLAVE_API_STANDARDIZATION.md` - Standardization across all slaves


## Installation & Setup

1. Install MicroPython on all Raspberry Pi Picos
2. Copy the appropriate firmware to each Pico:
   - **Master Pico:** `i2c_master_api.py`
   - **Stepper Pico:** `i2c_slave_stepper.py`
   - **Actuator Pico:** `i2c_slave_actuator.py`
   - **Radar Pico:** `uart_radar_slave.py`
3. Connect all Picos:
   - I2C slaves to Master Pico via SDA (GP0) and SCL (GP1)
   - Radar Pico to Master Pico via UART1 (TX: GP4, RX: GP5)
   - All Picos share common ground (GND)
   - All Picos powered by 5V
4. Connect master Pico to server via USB
5. On the server, use the provided Node.js serial utility to communicate with the master Pico

## Flashing Picos with Firmware

### Method 1: Using Thonny IDE (Easiest)

1. **Install Thonny:** Download from https://thonny.org/
2. **Connect Pico to PC via USB**
3. **Open Thonny** and select your Pico from the interpreter menu (bottom-right)
4. **Open firmware file** (e.g., `i2c_slave_stepper.py`)
5. **Save to device:** File → Save as → Choose device → select filename as `main.py`
6. **Restart Pico** - disconnect/reconnect USB or use Ctrl+D in Thonny REPL
7. **Verify:** Open serial monitor in Thonny to see debug output

### Method 2: Using mpremote (Command Line)

1. **Install mpremote:**
   ```bash
   pip install mpremote
   ```

2. **Connect Pico via USB**

3. **Copy firmware to Pico:**
   ```bash
   # For Master Pico
   mpremote cp src/i2c_master_api.py :main.py
   
   # For Stepper Pico
   mpremote cp src/i2c_slave_stepper.py :main.py
   
   # For Actuator Pico
   mpremote cp src/i2c_slave_actuator.py :main.py
   
   # For Radar Pico
   mpremote cp src/uart_radar_slave.py :main.py
   ```

4. **Test via REPL:**
   ```bash
   mpremote repl
   # Type HELP to see commands
   ```

### Method 3: Using rshell (Advanced)

1. **Install rshell:**
   ```bash
   pip install rshell
   ```

2. **Connect Pico and launch rshell:**
   ```bash
   rshell
   ```

3. **Copy firmware file:**
   ```bash
   cp src/i2c_master_api.py /pyboard/main.py
   ```

4. **Reset Pico:**
   ```bash
   repl
   # Then press Ctrl+D to soft reboot
   ```

### Method 4: Manual Copy via REPL

1. **Connect Pico to PC via USB**
2. **Open any serial terminal** (PuTTY, VSCode, etc.) at 115200 baud
3. **You should see the `>>>` prompt** (MicroPython REPL)
4. **Enter this to create a new file:**
   ```python
   f = open('main.py', 'w')
   ```
5. **Copy the entire contents of your firmware file and paste it**
6. **Close the file:**
   ```python
   f.write(your_code_here)
   f.close()
   ```
7. **Soft reboot by pressing Ctrl+D**

### Method 5: Batch Update Script (PowerShell on Windows)

Create a script `flash_picos.ps1`:
```powershell
# Flash all Picos with different firmware
$picos = @(
    @{Port="COM5"; Firmware="src/i2c_master_api.py"; Name="Master"},
    @{Port="COM6"; Firmware="src/i2c_slave_stepper.py"; Name="Stepper"},
    @{Port="COM7"; Firmware="src/i2c_slave_actuator.py"; Name="Actuator"},
    @{Port="COM8"; Firmware="src/uart_radar_slave.py"; Name="Radar"}
)

foreach ($pico in $picos) {
    Write-Host "Flashing $($pico.Name) on $($pico.Port)..."
    mpremote connect $pico.Port cp $pico.Firmware :main.py
    Write-Host "Done!"
}
```

Run with:
```bash
powershell -ExecutionPolicy Bypass -File flash_picos.ps1
```

### Identifying Serial Ports

**On Windows (PowerShell):**
```powershell
Get-WmiObject Win32_SerialPort | Select-Object DeviceID, Description
```

**On macOS/Linux:**
```bash
ls -la /dev/tty.* 
# or
ls -la /dev/ttyUSB*
```

### Troubleshooting Flashing

**Pico not showing up as serial device:**
- Try a different USB cable (data cable, not just power)
- Hold BOOTSEL button while plugging in to enter bootloader mode
- Reinstall MicroPython firmware from https://micropython.org/download/rp2-pico/

**"Permission denied" when flashing:**
- On Linux: `sudo chmod 666 /dev/ttyUSB0`
- On Windows: Try running as Administrator

**Firmware file too large:**
- The Pico has ~1.6MB storage; check if your file is too large
- Remove unnecessary comments or split into multiple files

### Verify Firmware is Running

After flashing:
1. **Disconnect and reconnect USB**
2. **Open serial monitor at 115200 baud**
3. **Type `HELP` command**
4. **Should see the firmware's command list**
5. **Test a simple command like `STATUS`**

## USB Serial Testing

All Pico firmware files support interactive testing via USB serial. This allows you to test individual Picos without a full system setup.

### How to Test via USB:
1. Connect a Pico to your PC via USB
2. Open a serial monitor (VSCode, PuTTY, etc.) at **115200 baud**
3. Type commands to interact with the Pico in real-time
4. See real-time debug output with `[I2C]`, `[UART]`, or `[USB]` tags

### Master Pico Commands (`i2c_master_api.py`):
```
STEPPER_STATUS           # Get stepper position
MOVE_STEPPER:90          # Move stepper to 90°
ACTUATOR_STATUS          # Get actuator state
ACTUATE                  # Activate actuator
DEACTUATE                # Deactivate actuator
RADAR_STATUS             # Get latest radar data
HELP                     # Show all commands
```

### Stepper Pico Commands (`i2c_slave_stepper.py`):
```
STATUS                   # Get current position
MOVE:45                  # Move to 45°
HELP                     # Show commands
```

### Actuator Pico Commands (`i2c_slave_actuator.py`):
```
STATUS                   # Get current state (0/1)
ACTIVATE                 # Turn ON
DEACTIVATE               # Turn OFF
HELP                     # Show commands
```

### Radar Pico Commands (`uart_radar_slave.py`):
```
READ                     # Get current radar data
RANGE:150                # Set range to 150cm (test)
VEL:5.5                  # Set velocity to 5.5 m/s (test)
STATUS                   # Check operational status
HELP                     # Show commands
```

## Configuration

### I2C Addresses (Customizable)
Edit the firmware files to set custom I2C addresses if needed:
```python
STEPPER_ADDR = 0x10      # i2c_slave_stepper.py
ACTUATOR_ADDR = 0x12     # i2c_slave_actuator.py
RADAR_ADDR = 0x11        # i2c_slave_radar.py (if using I2C mode)
```

### UART Configuration
```python
# Master Pico UART0 (to Server)
UART(0, baudrate=115200, tx=Pin(16), rx=Pin(17))

# Master Pico UART1 (from Radar Pico)
UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
```

### Edit `config/settings.py` for additional customization:

```python
# Choose radar type
RADAR_TYPE = "RCWL0516"  # or "CQROBOT"

# Servo settings
SERVO_PIN = 16
SERVO_NEUTRAL_POSITION = 90
SERVO_ACTIVE_POSITION = 45

# UART communication with Pi4
UART_TO_PI4_TX = 16
UART_TO_PI4_RX = 17
UART_TO_PI4_BAUDRATE = 115200

# Detection parameters
DETECTION_THRESHOLD = 1  # Minimum sensors for activation
SCAN_INTERVAL_MS = 100   # Scan frequency
```


## Usage

### I2C Slave Firmware
All I2C slave Picos can be tested via USB serial. Connect via USB and type commands (see USB Serial Testing section above).

### UART Radar Slave Firmware
The radar Pico continuously transmits radar data via UART1 to the master Pico. Test with USB serial for parameter adjustment.

### Master Pico Firmware
The master Pico:
1. Listens for commands from the server via UART0 (USB/UART connection)
2. Relays commands to I2C slaves (stepper, actuator)
3. Reads radar data from UART1 (radar Pico)
4. Aggregates all data and sends responses back to server
5. Supports interactive USB serial testing

### Node.js Server Communication
Use the utility in `server/utils/picoMasterSerial.js`:
```js
const { sendCommand } = require('./utils/picoMasterSerial')
sendCommand('STEPPER_STATUS').then(console.log)
sendCommand('MOVE_STEPPER:90').then(console.log)
sendCommand('ACTUATE').then(console.log)
sendCommand('RADAR_STATUS').then(console.log)
```

### Testing Components Individually

#### Test Stepper Pico
1. Flash `i2c_slave_stepper.py` to Pico
2. Connect via USB
3. Open serial monitor (115200 baud)
4. Type: `MOVE:45` then press Enter
5. See output: `[USB] Received: MOVE:45` and `[USB] Moving to 45°`

#### Test Actuator Pico
1. Flash `i2c_slave_actuator.py` to Pico
2. Connect via USB
3. Open serial monitor (115200 baud)
4. Type: `ACTIVATE` then press Enter
5. See output confirming activation

#### Test Radar Pico
1. Flash `uart_radar_slave.py` to Pico
2. Connect via USB
3. Open serial monitor (115200 baud)
4. Type: `RANGE:200` to set test range
5. Type: `READ` to see current values

#### Test Master Pico with Full System
1. Flash `i2c_master_api.py` to master Pico
2. Connect all slave Picos via I2C/UART
3. Connect master Pico to PC via USB
4. Open serial monitor (115200 baud)
5. Type: `HELP` to see all commands
6. Test I2C slaves: `STEPPER_STATUS`, `MOVE_STEPPER:90`, `ACTUATE`
7. Test UART radar: `RADAR_STATUS`


## System Behavior (New Modular Architecture)

1. **Initialization:** Master Pico initializes all I2C slaves and UART radar connection
2. **Command Reception:** Server sends commands to master Pico via UART0 (USB)
3. **I2C Relay:** Master Pico relays commands to I2C slaves (stepper @ 0x10, actuator @ 0x12)
4. **UART Data:** Master Pico continuously reads radar data from radar Pico via UART1
5. **Data Aggregation:** Master Pico combines all data (I2C responses + UART radar data)
6. **Response Transmission:** Master Pico sends aggregated response back to server
7. **Real-time Updates:** Server broadcasts updates to client via WebSocket
8. **Error Handling:** All Picos support USB serial for debugging and manual intervention

## Troubleshooting

### Common Issues

**I2C Slaves Not Responding:**
- Check I2C wiring (SDA/SCL connections)
- Verify pull-up resistors (typically 4.7k Ohm)
- Test each slave individually via USB serial
- Confirm I2C addresses match firmware (stepper 0x10, actuator 0x12)

**Radar Pico Not Sending Data:**
- Check UART1 wiring (TX: GP4, RX: GP5)
- Verify baud rate is 115200 on both master and radar Pico
- Test radar Pico via USB serial: type `READ`
- Check master Pico USB serial for `[UART] Sent:` messages

**Master Pico Not Responding via USB:**
- Verify USB connection (should appear as serial device)
- Check baud rate is 115200
- Type `HELP` to see available commands
- Look for debug messages starting with `[USB]`, `[I2C]`, or `[UART]`

**Commands Not Working Over UART (from Server):**
- Test with USB serial first to confirm Pico works
- Verify UART0 pins (TX: GP16, RX: GP17)
- Confirm server is sending commands in correct format
- Check Node.js serial utility logs

### USB Serial Testing Tips

1. **See Real-Time Debug Output:**
   - Open PuTTY, VSCode Terminal, or similar
   - Set baud rate to 115200
   - Type `HELP` to list commands
   - Commands are tagged with `[I2C]`, `[UART]`, or `[USB]`

2. **Test Individual Components:**
   - Flash each Pico with its firmware separately
   - Connect via USB and test with serial monitor
   - No need for I2C/UART wiring to test individual Pico

3. **Monitor System Behavior:**
   - Connect master Pico via USB
   - Send commands from server
   - Watch debug output in serial monitor
   - See which I2C slaves respond and UART data received

### Debug Mode

Enable additional debug output by adding to any firmware file:
```python
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

## Performance Notes

- **I2C Communication:** ~100ms scan interval (SDA/SCL @ 100kHz)
- **UART Radar:** ~100ms data transmission interval (115200 baud)
- **Master Pico Polling:** ~10ms loop cycle
- **Stepper Response Time:** ~200ms typical
- **Actuator Response Time:** ~50ms typical
- **Power Consumption:** ~100mA total (all Picos + sensors)

## Safety Considerations

- Ensure proper power supply ratings for all devices
- Use appropriate pull-up resistors on I2C bus (typically 4.7kΩ)
- Test servo/actuator limits before deployment
- Verify all UART connections (TX/RX not swapped)
- Use common ground for all Picos
- External antenna for radar may interfere with I2C/UART signals


## Future Enhancements

- Auto-discovery of slave Picos (broadcast/probe)
- I2C error handling and automatic retries
- UART error detection and recovery
- Fallback modes (I2C radar mode if UART fails)
- Wireless master-server communication (WiFi Pico W)
- Web-based serial terminal for remote Pico debugging
- Multi-master failover system

---

**Current Status:** Modular I2C+UART master/slave architecture with USB serial testing support. All slave Picos and master Pico fully functional and debuggable via USB.

For legacy single-Pico operation, see previous commits.