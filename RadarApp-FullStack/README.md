# Raspberry Pi Radar Full Stack Application and Stepper Controller


**New Architecture (2026): Modular Pico I2C Master/Slave System**

This project now supports a modular hardware architecture using multiple Raspberry Pi Picos communicating over I2C. Each hardware function (stepper, radar, actuator) is managed by a dedicated Pico (slave), with a master Pico aggregating all data and relaying commands/status to the server via UART/USB. The Node.js backend communicates only with the master Pico, which acts as a bridge to all hardware.


## Hardware Requirements (Updated)

- Raspberry Pi 4
- Stepper motor controller/driver
- Stepper motor
- Radar module (RCWL-0516 or CQRobot)
- Multiple Raspberry Pi Picos:
  - 1x Master Pico (I2C master, UART/USB to server)
  - 1x Stepper Pico (I2C slave, controls stepper motor)
  - 1x Radar Pico (I2C slave, handles radar sensors)
  - 1x Actuator Pico (I2C slave, controls actuator/servo)
- I2C wiring (SDA/SCL, common GND)
- Optional: External antenna for better range

## Architecture


**Communication Flow:**
Client → Server → Master Pico (UART/I2C) → Slave Picos (Stepper, Actuator via I2C, Radar via UART)

- **Web Interface** sends hardware commands
- **Node.js Server** relays commands to Master Pico via UART/USB
- **Master Pico** acts as I2C master, relays commands to slave Picos and aggregates data
- **Stepper/Actuator Picos** (I2C Slaves) execute commands and report status via I2C
- **Radar Pico** (UART Slave) communicates with Master Pico via UART
- **Real-time Updates** flow back through the same path to update the web interface

```
┌────────────────────┐      ┌────────────────────┐      ┌────────────────────┐
│   Vue.js Client    │◄────┤   Node.js Server   │◄────┤   Hardware Layer    │
│  • Dashboard       │      │  • Express API     │      │  • Stepper Motor   │
│  • Real-time UI    │      │  • Socket.IO       │      │  • Actuator        │
│  • Controls        │      │  • Controllers     │      │  • Radar (UART)    │
└────────────────────┘      └────────────────────┘      └────────────────────┘
                                 │
                                 │ UART
                                 ▼
                        ┌────────────────────┐
                        │   Master Pico      │
                        │   (I2C Master)     │
                        └────────────────────┘
                          │      │      │
                   I2C    │      │      │ UART
                  ┌───────┘      │      └─────────────┐
                  ▼              ▼                    │
         ┌──────────────┐  ┌──────────────┐           │
         │ Stepper Pico │  │ Actuator Pico│           │
         │ (I2C Slave)  │  │ (I2C Slave)  │           │
         └──────────────┘  └──────────────┘           │
                                                      │
                                               ┌──────────────┐
                                               │  Radar Pico  │
                                               │ (UART Slave) │
                                               └──────────────┘
```

## Features

### 🔧 Stepper Motor Control
- **Continuous rotation** until user command to stop
- **Speed control** (RPM adjustment)
- **Direction control** (clockwise/counterclockwise)
- **Manual stepping** for precise positioning
- **Real-time feedback** on position and status

### 📡 Radar System
- **Dual radar sources** (local USB + Raspberry Pi Pico via UART)
- **Real-time data acquisition** from radar modules
- **Live visualization** with radar sweep display
- **Detection tracking** and alerts
- **Data logging** and export capabilities
- **Configurable parameters** (sensitivity, range, etc.)


### 🔌 Pico Integration (I2C Master/Slave)
- **All hardware control** (stepper, radar, actuator) is routed through the master Pico
- **I2C protocol** for robust, scalable hardware communication
- **Single UART/USB connection** between server and master Pico
- **Real-time data aggregation** from all slave Picos
- **Automatic device discovery and error handling** (planned)

### 📊 Dashboard & Monitoring
- **System overview** with all components status
- **Real-time charts** and data visualization
- **Alert notifications** for system events
- **Performance monitoring** and diagnostics

## Control Flow

### Remote Servo Control
1. **Web Interface** - User clicks servo control button
2. **WebSocket** - Client emits servo command to server
3. **Server Processing** - Node.js receives and validates command
4. **UART Transmission** - Server sends JSON command to Pico
5. **Pico Execution** - Pico processes command and moves servo
6. **Status Feedback** - Pico sends servo position back through UART
7. **Real-time Update** - Web interface shows updated servo status

### Radar Data Streaming
1. **Pico Sensors** - Continuously reads radar modules (RCWL-0516/CQRobot)
2. **Data Processing** - Pico processes readings and detects motion
3. **UART Stream** - Real-time radar data sent to Pi4 every 250ms
4. **Server Relay** - Node.js forwards data via WebSocket
5. **Live Visualization** - Web dashboard updates radar display and charts
6. **Alert System** - Motion detection triggers immediate notifications

## Installation

### Prerequisites
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js (version 16+)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install required system packages
sudo apt-get install -y build-essential python3-dev
```

### Project Setup
```bash
# Clone/navigate to project directory
cd RadarApp-FullStack

# Install server dependencies
npm run install:server

# Install client dependencies
npm run install:client

# Build client application
npm run build

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Environment Configuration
Create a `.env` file in the project root:
```bash
# Server Configuration
PORT=3000
NODE_ENV=production
CLIENT_URL=http://localhost:8080

# Hardware Configuration
STEPPER_PINS=18,19,20,21
STEPPER_ENABLE_PIN=22
RADAR_SERIAL_PORT=/dev/ttyUSB0
RADAR_BAUD_RATE=115200

# UART Communication with Raspberry Pi Pico
PICO_UART_PORT=/dev/ttyAMA0
PICO_UART_BAUD_RATE=115200
PICO_UART_ENABLED=true
PICO_DATA_TIMEOUT=5000

# Logging
LOG_LEVEL=info
```


```
┌────────────────────┐      ┌────────────────────┐      ┌────────────────────┐
│   Vue.js Client    │◄────┤   Node.js Server   │◄────┤   Hardware Layer    │
│  • Dashboard       │      │  • Express API     │      │  • Stepper Motor   │
│  • Real-time UI    │      │  • Socket.IO       │      │  • Actuator        │
│  • Controls        │      │  • Controllers     │      │  • Radar (UART)    │
└────────────────────┘      └────────────────────┘      └────────────────────┘
                                 │
                                 │ UART
                                 ▼
                        ┌────────────────────┐
                        │   Master Pico      │
                        │   (I2C Master)     │
                        └────────────────────┘
                          │      │      │
                   I2C    │      │      │ UART
                  ┌───────┘      │      └─────────────┐
                  ▼              ▼                    │
         ┌──────────────┐  ┌──────────────┐           │
         │ Stepper Pico │  │ Actuator Pico│           │
         │ (I2C Slave)  │  │ (I2C Slave)  │           │
         └──────────────┘  └──────────────┘           │
                                                      │
                                               ┌──────────────┐
                                               │  Radar Pico  │
                                               │ (UART Slave) │
                                               └──────────────┘
```
```ini
[Unit]
Description=Radar Control System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/RadarApp-FullStack
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable radar-system.service
sudo systemctl start radar-system.service
```

## API Endpoints

### System
- `GET /api/status` - System status
- `GET /api/health` - Health check
- `POST /api/restart` - Restart system
- `POST /api/shutdown` - Shutdown system

### Stepper Motor
- `GET /api/stepper/status` - Get motor status
- `POST /api/stepper/start` - Start continuous rotation
- `POST /api/stepper/stop` - Stop motor
- `PUT /api/stepper/speed` - Set speed (RPM)
- `PUT /api/stepper/direction` - Set direction (1 or -1)
- `POST /api/stepper/step` - Manual step control
- `POST /api/stepper/reset` - Reset step counter

### Radar
- `GET /api/radar/status` - Get radar status
- `POST /api/radar/start` - Start scanning
- `POST /api/radar/stop` - Stop scanning
- `GET /api/radar/data` - Get recent data
- `GET /api/radar/stats` - Get statistics
- `PUT /api/radar/config` - Update configuration
- `DELETE /api/radar/data` - Clear data
- `GET /api/radar/export` - Export data


### Pico Communication (New)
- `GET /api/pico/status` - Get master Pico connection status
- `POST /api/pico/command` - Send command to master Pico (relayed to correct slave)
- `POST /api/pico/request-status` - Request status from master Pico (aggregates from all slaves)
- `POST /api/pico/stepper/move` - Move stepper via master/slave relay
- `POST /api/pico/radar/read` - Read radar data via master/slave relay
- `POST /api/pico/actuator/activate` - Control actuator via master/slave relay

## WebSocket Events

### Client → Server → Pico (Command Chain)
```javascript
// Remote servo control through command chain
socket.emit('pico:controlServo', 'activate')    // Client sends to server
// → Server forwards via UART to Pico → Pico moves servo → Status returns

// Request real-time status from Pico
socket.emit('pico:requestStatus')               // Triggers status request chain

// Send custom commands to Pico
socket.emit('pico:sendCommand', { 
  command: 'radar_config', 
  params: { sensitivity: 75 } 
})

// Stepper control (local to Pi4)
socket.emit('stepper:start', { speed: 100, direction: 1 })
socket.emit('stepper:stop')
socket.emit('stepper:setSpeed', 150)
socket.emit('stepper:setDirection', -1)

// Local radar control
socket.emit('radar:start')
socket.emit('radar:stop')
socket.emit('radar:configure', { sensitivity: 75 })

// System control
socket.emit('system:restart')
socket.emit('system:shutdown')
```

### Server → Client (Real-time Data Flow)
```javascript
// Real-time Pico data streaming
socket.on('pico:radarData', (data) => {
  // Live radar readings from Pico sensors
  // Updates every 250ms with detection status
})

socket.on('pico:detection', (data) => {
  // Immediate motion detection alerts from Pico
  // Triggers when motion threshold exceeded
})

socket.on('pico:servoStatus', (data) => {
  // Real-time servo position and activation status
  // Updated whenever servo moves or changes state
})

socket.on('pico:connected', () => {
  // UART connection established with Pico
})

socket.on('pico:disconnected', () => {
  // UART connection lost - triggers reconnection
})

// System and local component events
socket.on('system:status', (data) => { ... })
socket.on('stepper:started', (data) => { ... })
socket.on('stepper:stopped', (data) => { ... })
socket.on('stepper:progress', (data) => { ... })
socket.on('radar:data', (data) => { ... })        // Local radar
socket.on('radar:detection', (data) => { ... })   // Local radar
socket.on('radar:scanStarted', (data) => { ... }) // Local radar
```



### Hardware Connections (Slip Ring Wiring Example)

#### 6-Wire Slip Ring Recommended Wiring
```
1. SDA (I2C Data)
2. SCL (I2C Clock)
3. TX (UART Transmit)
4. RX (UART Receive)
5. GND (Common Ground)
6. 5V (Power for all devices)
```

- **I2C Bus:** SDA, SCL
- **UART Bus:** TX, RX
- **Power:** 5V and GND shared by all devices

This setup allows you to run both I2C and UART through the slip ring, with a dedicated wire for 5V power and ground. One wire is left over for future expansion or additional signals if needed.

#### Stepper, Radar, Actuator Picos
- Each Pico is flashed with its respective `i2c_slave_*.py` firmware and unique I2C address

#### Master Pico
- Flashed with `i2c_master_api.py` firmware
- Connects to server via USB (UART)

#### Power Supply
- **5V/3A** for Raspberry Pi
- **3.3V/5V** for each Pico and sensors (check specs)

## Configuration Files

### Server Configuration (`server/config/`)
- Hardware pin assignments
- Serial port settings
- Network configuration
- Logging levels

### Client Configuration (`client/src/config/`)
- API endpoints
- WebSocket settings
- UI themes and layouts

## Troubleshooting

### Common Issues

**Stepper motor not responding:**
```bash
# Check GPIO permissions
sudo usermod -a -G gpio pi
sudo chmod 666 /dev/gpiomem

# Verify pin connections
gpio readall
```

**Radar module connection issues:**
```bash
# List serial devices
ls -la /dev/tty*

# Check device permissions
sudo usermod -a -G dialout pi

# Test serial connection
sudo minicom -D /dev/ttyUSB0 -b 115200
```

### Performance Optimization

**For better performance:**
- Use Class 10 SD card (minimum)
- Enable GPU memory split: `sudo raspi-config` → Advanced → Memory Split → 64
- Disable unnecessary services if not needed

## Development

### Adding New Features
1. **Server side:** Add controllers in `server/controllers/`
2. **Client side:** Add components in `client/src/components/`
3. **API routes:** Update `server/routes/`
4. **State management:** Extend Vuex modules

### Testing
```bash
# Run server tests
npm test

# Run client tests  
cd client && npm test

# Integration tests
npm run test:integration
```

## Security Considerations

- Change default passwords
- Use HTTPS in production
- Implement proper authentication
- Regular security updates
- Network firewall configuration


## License

MIT License - see LICENSE file for details

---

**This README reflects the new modular I2C master/slave architecture. For legacy single-Pico operation, see previous commits.**

## Support

For support and questions:
1. Check troubleshooting section
2. Review hardware connections
3. Check system logs: `journalctl -u radar-system.service`
4. Monitor application logs: `tail -f logs/combined.log`