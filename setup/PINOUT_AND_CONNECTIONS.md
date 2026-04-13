# Pinout & Connection Reference

Complete master and endpoint communication pinouts for the Radar Project system.

---

## System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                    RASPBERRY PI 4 (Server)                           │
│                    UART ↔ Master Pico GPIO16/17                      │
│                    460800 baud (high-speed link)                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                │ (GPIO pins)
                                │
┌───────────────────────────────┴─────────────────────────────────────┐
│                         Master Pico (I2C Master)                    │
│                         [i2c_Master_API]                            │
├─────────────────────────────────────────────────────────────────────┤
│  I2C0: GPIO0(SDA)─────┬────────────────────────────────────┬────────│
│         GPIO1(SCL)    │                                    │        │
│                       │                                    │        │
│  UART0: GPIO16(TX)┐   │  ┌─── Stepper Pico───────────────┐ │        │
│         GPIO17(RX)├───┼──┼─ I2C Slave 0x10 (GPIO0/1) ────┼──────────│
│    (Server + Debug)   │  │  GPIO5: PUL               │   │ │        │
│  UART1: GPIO4(TX) ┐   │  │  GPIO6: DIR               │   │ │        │
│         GPIO5(RX) └───┼──┼─ GPIO7: ENA               │   │ │        │
│                       │  │  GPIO20: home_SENSOR      │   │ │        │
│                       │  └───────────────────────────────┘ │        │
│                       │                                    │        │
│                       │  ┌─── Actuator Pico──────────┐     │        │
│                       └──┤ I2C Slave 0x12 (GPIO0/1)    ────┤────────│
│                          │  GPIO2: PWM (Servo)         │   │        │
│                          └─────────────────────────────┘   │        │
│                                                            │        │
│                       ┌─── Radar Pico──────────────┐       │        │
│                       │ UART Slave (GPIO4/5)       │───────┘        │
│                       │  115200 baud               │                │
│                       └────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Master Pico (I2C Master API)

**Location:** `src/i2c_Master_API/main.py`

**Function:** Central controller that communicates with all slave devices

### Communications

#### I2C0 Interface
- **Role:** Master I2C bus
- **Frequency:** 100 kHz
- **Protocol:** i2c_bus (built-in SMBus compatible)

| Pin | GPIO | Function | Description |
|-----|------|----------|-------------|
| SDA | 0 | I2C Data | Connect to all I2C Slaves |
| SCL | 1 | I2C Clock | Connect to all I2C Slaves |

**Pull-up Resistors Required:** 4.7kΩ each (may already be on slave devices)

#### UART0 (Dual Purpose: Server + Debug)
- **Baud Rate:** 460800
- **Purpose:** High-speed serial communication with Pi 4 server AND debug output to terminal/USB
- **Connection:** Shared multiplexed connection (Pi 4 primary, debug secondary)

| Pin | GPIO | Function | Description |
|-----|------|----------|-------------|
| TX | 16 | Transmit | → Pi 4 RX / USB Terminal |
| RX | 17 | Receive | ← Pi 4 TX / USB Terminal |

#### UART1 (Radar Communication)
- **Baud Rate:** 115200
- **Purpose:** Serial communication with radar slave
- **Connected to:** Radar Pico (GPIO4/5)

| Pin | GPIO | Function | Description |
|-----|------|----------|-------------|
| TX | 4 | Transmit | → Radar RX |
| RX | 5 | Receive | ← Radar TX |

### Power

| Pin | Voltage | Function |
|-----|---------|----------|
| VSYS/VBUS | 5V | Input power |
| 3V3 | 3.3V | Regulated output for sensors |
| GND | 0V | Ground (common reference) |

---

## Raspberry Pi 4 (Server & Application Controller)

**Location:** `RadarApp-FullStack/`

**Function:** High-level application server that sends commands to Master Pico and receives sensor/system data for web UI and real-time control

### UART0 Connection (Master Pico)

**Communication Link:** High-speed bidirectional UART (GPIO pins)
- **Baud Rate:** 460800 bps
- **Distance:** Local (co-located on same board/enclosure)
- **Latency:** <5ms for command/response cycles

| Pi 4 Pin | Function | Connection | Pico Pin |
|----------|----------|-----------|----------|
| GPIO14 (TX) | Transmit | → Master GPIO16 (RX) | 25 |
| GPIO15 (RX) | Receive | ← Master GPIO17 (TX) | 26 |
| GND | Ground | Master GND | - |

**Protocol:** Binary or JSON-based command/response
- **Commands:** Motor position, actuator control, system queries
- **Responses:** Sensor readings, firmware status, motion complete events

### Network Interface

| Interface | Function |
|-----------|----------|
| Ethernet / WiFi | Web UI access, API endpoints |
| UART (GPIO14/15) | Master Pico control & telemetry |

### Server Software

**Node.js Application Stack:**
- `server/index.js` - Express server
- `server/controllers/` - Request handlers
- `server/routes/` - API endpoints
- `server/utils/picoMasterSerial.js` - UART communication layer

**Client:**
- Vue.js web application
- Real-time WebSocket updates
- Dashboard, radar control, stepper control, settings

### Power

| Source | Voltage | Function |
|--------|---------|----------|
| USB-C | 5V 3A+ | Pi 4 main power |
| System GND | 0V | Common ground with Pico |

---

## Stepper Pico (I2C Slave - Stepper Motor Controller)

**Location:** `src/i2c_Slave_Stepper/main.py`

**I2C Address:** `0x10` (configurable in code)

**Function:** Controls stepper motor with home position sensing

### I2C Interface

| Pin | GPIO | Function  | Connection     |
|-----|------|---------- |-----------     |
| SDA | 0    | I2C Data  | → Master GPIO0 |
| SCL | 1    | I2C Clock | → Master GPIO1 |
| GND | Any  | Ground    | → Master GND   |

**Note:** Uses default I2C0 on Pico (no explicit configuration needed)

### Motor Control Pins

| Pin | GPIO | Function | Connection | Details |
|-----|------|----------|-----------|---------|
| PUL | 5 | Pulse (Step) | → Stepper Driver | PWM signal for steps |
| DIR | 6 | Direction | → Stepper Driver | HIGH=CW, LOW=CCW |
| ENA | 7 | Enable | → Stepper Driver | HIGH=enabled, LOW=disabled |

### Sensor Input

| Pin | GPIO | Type | Function | Details |
|-----|------|------|----------|---------|
| home | 20 | Input | Home Sensor | OMRON LJ12A3-4Z/BY (PNP) |

**Sensor Wiring:**
- Brown wire: 6-36V DC external power
- Blue wire: GND (common ground)
- Black wire: GPIO 20 (LOW when metal detected)

### Motor Configuration

**Stepper Motor:**
- Type: NEMA stepper (bipolar)
- Steps/Rev: 200
- Degrees/Step: 1.8°

**Gearing:**
- Configuration: 20T (motor) → 60T (output) = 3:1 reduction
- Output Steps/Rev: 600
- Output Degrees/Step: 0.6°

### Power Requirements

| Pin | Voltage | Function |
|-----|---------|----------|
| VSYS | 5V | Pico power |
| 3V3 | 3.3V | GPIO opetration |
| GND | 0V | Ground (common with stepper driver) |

---

## Actuator Pico (I2C Slave - Servo/Retract Controller)

**Location:** `src/i2c_Slave_Actuator/main.py`

**I2C Address:** `0x12` (configurable in code)

**Function:** Controls servo/retractable mechanism (3-wire actuator)

### I2C Interface

| Pin | GPIO | Function | Connection |
|-----|------|----------|-----------|
| SDA | 0 | I2C Data | → Master GPIO0 |
| SCL | 1 | I2C Clock | → Master GPIO1 |
| GND | Any | Ground | → Master GND |

**Note:** Uses default I2C0 on Pico (no explicit configuration needed)

### Actuator Control

| Pin | GPIO | Type | Function | Details |
|-----|------|------|----------|---------|
| PWM | 2 | PWM Output | Servo Signal | RC Servo standard (50Hz) |

**RC Servo Wiring (3-wire connector):**
- Brown/Black: GND
- Red: 5V
- Yellow: PWM Signal (GPIO 2)

**Servo PWM Mapping:**
- 1.0ms pulse (duty 2500): Retracted position
- 1.5ms pulse (duty 3750): Center position  
- 2.0ms pulse (duty 5000): Extended position
- Frequency: 50Hz

**Servo Range:**
- Angle: 0-180°
- Internal Control: 0-100 (stored as degrees/scaling)

### Power Requirements

| Pin | Voltage | Function |
|-----|---------|----------|
| VSYS | 5V | Pico power |
| 3V3 | 3.3V | GPIO operation |
| GND | 0V | Ground (common with servo) |

---

## Radar Pico (UART Slave - Radar Sensor)

**Location:** `src/uart_Slave_Radar/main.py`

**Function:** Reads radar sensor and transmits detection data via serial

### UART1 Interface

| Pin | GPIO | Function | Connection |
|-----|------|----------|-----------|
| TX | 4 | Transmit | → Master RX17* |
| RX | 5 | Receive | ← Master TX16* |
| GND | Any | Ground | → Master GND |

*Master uses UART1 on GPIO4/5, different from debug UART0

**UART Settings:**
- Baud Rate: 115200
- Data Bits: 8
- Stop Bits: 1
- Parity: None

### Data Protocol

**Format:** `distance,confidence,movement\r\n`

Example outputs:
```
500,85,0\r\n          (500cm, 85% confidence, no movement)
1200,90,1\r\n         (1200cm, 90% confidence, motion detected)
```

### Sensor Connection

| Pin | Function | Voltage |
|-----|----------|---------|
| VCC | Power | 5V (external) |
| GND | Ground | 0V (common) |
| TX | Data Output | 3.3V logic |
| RX | Data Input | 3.3V logic |

### Power Requirements

| Pin | Voltage | Function |
|-----|---------|----------|
| VSYS | 5V | Pico power |
| 3V3 | 3.3V | GPIO operation |
| GND | 0V | Ground |

---

## Wiring Diagram Summary

### Main Bus Connection (I2C0)

```
    Master Pico (GPIO 0,1)
         |         |
         |         |
      [4.7kΩ]   [4.7kΩ]  ← Pull-up resistors
         |         |
    ┌────┴─────────┴────┐
    │                   │
    │    I2C BUS 0      │
    │                   │
    ├─────┬─────────────┤
    │     │             │
Stepper  Actuator      GND
 0x10     0x12

(All devices share GPIO0 SDA and GPIO1 SCL)
```

### Serial Connections

**UART0 (Master Pico ↔ Pi 4 Server) - 460800 baud:**
```
Master Pico              Raspberry Pi 4
GPIO16 (TX) ───────────→ RX pin
GPIO17 (RX) ←──────────── TX pin
GND ────────────────────── GND
```

**UART1 (Master Pico ↔ Radar Pico) - 115200 baud:**
```
Master Pico              Radar Pico
GPIO4 (TX) ──────────→ GPIO5 (RX)
GPIO5 (RX) ←────────── GPIO4 (TX)
GND ─────────────────── GND
```

### Full Block Diagram

```
┌────────────────────────────┐
│   RASPBERRY PI 4 (Server)  │
│     Node.js Application    │
│  (GPIO serial interface)   │
└────────────┬───────────────┘
             │ UART 460800
             │ GPIO Pins
             │
┌────────────┴──────────────────────────────────────────────┐
│ master PICO - Central Control Hub                         │
│                                                           │
│  I2C Bus (100kHz)              UART Connections          │
│  ├─ GPIO0 (SDA) ────┬──────┐   ├─ UART0 (460800)        │
│  ├─ GPIO1 (SCL) ────┤      │   │  GPIO16/17 (Pi 4+USB)  │
│  └─ GND             │      │   │                        │
│                     │      │   └─ UART1 (115200)        │
│                     │      │      GPIO4/5 (Radar)      │
└─────────────────────┼──────┼────────────────────────────┘
                      │      │
          ┌───────────┴─┐    ├─────────────┐
          │             │    │             │
      ┌───┴────┐   ┌────┴──┐│  ┌─────────┴──────┐
      │stepper │   │servo   │radar           │
      │ 0x10   │   │  0x12     │(UART Slave)    │
      │Motors  │   │ Servo     │                │
      │Sensors │   │ Control   │Sensor Data     │
      └────────┘   └───────────┘ Distance/Conf  │
                                │                │
                                └────────────────┘
```

---

## Raspberry Pi Pico Physical Pinout

**Complete 40-pin layout (with GPIO assignments):**

```
        ┌──────────────────────────────────────┐
        │   RASPBERRY PI PICO (Top View)       │
        │                                      │
  GND ──│ 1                                 40 │── VBUS (5V IN)
GPIO0 ──│ 2                                 39 │── 3V3OUT
GPIO1 ──│ 3                                 38 │── GND
GPIO2 ──│ 4                                 37 │── GPIO28
GPIO3 ──│ 5                                 36 │── GPIO27
  GND ──│ 6                                 35 │── GPIO26
GPIO4 ──│ 7                                 34 │── GND
GPIO5 ──│ 8                                 33 │── GPIO22
  GND ──│ 9                                 32 │── GPIO21
GPIO6 ──│10                                 31 │── GPIO20
GPIO7 ──│11                                 30 │── GND
  GND ──│12                                 29 │── GPIO19
GPIO8 ──│13                                 28 │── GPIO18
GPIO9 ──│14                                 27 │── GND
  GND ──│15                                 26 │── GPIO17
GPIO10 ─│16                                 25 │── GPIO16
GPIO11 ─│17                                 24 │── GND
  GND ──│18                                 23 │── GPIO15
GPIO12 ─│19                                 22 │── GPIO14
GPIO13 ─│20                                 21 │── GND
        └──────────────────────────────────────┘
```

### Master Pico Connections

| Physical Pin | GPIO | Function | Device           | Purpose |
|--------------|------|----------|------------------|---------|
| 1            | -    | GND      | System           | Ground reference |
| 2            | 0    | I2C0 SDA | Stepper/Actuator | I2C Data line |
| 3            | 1    | I2C0 SCL | Stepper/Actuator | I2C Clock line |
| 7            | 4    | UART1 TX | Radar            | Serial Transmit |
| 8            | 5    | UART1 RX | Radar            | Serial Receive |
| 25           | 16   | UART0 TX | Pi 4 Server      | High-speed server comm (460800) |
| 26           | 17   | UART0 RX | Pi 4 Server      | High-speed server comm (460800) |
| 40           | -    | VBUS     | Power            | 5V Input |
| 39           | -    | 3V3OUT   | Power            | 3.3V Output |

### Stepper Pico Connections

| Physical Pin | GPIO | Function | Peripheral | Details |
|--------------|------|----------|-----------|---------|
| 1 | - | GND | System | Ground |
| 2 | 0 | I2C0 SDA | Master | I2C Data |
| 3 | 1 | I2C0 SCL | Master | I2C Clock |
| 7 | 4 | - | - | Unused |
| 8 | 5 | PUL | Stepper Driver | Pulse (Step) |
| 11 | 7 | ENA | Stepper Driver | Enable |
| 10 | 6 | DIR | Stepper Driver | Direction |
| 31 | 20 | home_SENSOR | OMRON | Inductive sensor |
| 40 | - | VBUS | Power | 5V |
| 39 | - | 3V3OUT | Power | 3.3V |

**Stepper Motor Wiring:**
- PUL (Pin 8, GPIO5) → Stepper driver PUL input
- DIR (Pin 10, GPIO6) → Stepper driver DIR input
- ENA (Pin 11, GPIO7) → Stepper driver ENA input
- GND (Pin 1) → Stepper driver GND

**Home Sensor Wiring (OMRON LJ12A3-4Z/BY):**
- Brown wire → 5V power (external 6-36V)
- Blue wire → GND (Pin 1 or Pin 6)
- Black wire → GPIO20 (Pin 31)

### Actuator Pico Connections

| Physical Pin | GPIO | Function | Peripheral | Details |
|--------------|------|----------|-----------|---------|
| 1 | - | GND | System | Ground |
| 2 | 0 | I2C0 SDA | Master | I2C Data |
| 3 | 1 | I2C0 SCL | Master | I2C Clock |
| 4 | 2 | PWM | RC Servo | Control signal |
| 40 | - | VBUS | Power | 5V |
| 39 | - | 3V3OUT | Power | 3.3V |

**Servo Wiring (3-wire connector):**
- Brown/Black wire → GND (Pin 1 or 6)
- Red wire → 5V power (external or Pin 40)
- Yellow wire → GPIO2 (Pin 4) PWM signal

### Radar Pico (UART) Connections

| Physical Pin | GPIO | Function | Connection | Details |
|--------------|------|----------|-----------|---------|
| 1 | - | GND | Master Pin 1 | Ground |
| 7 | 4 | UART1 TX | Master GPIO5(RX) | Serial TX |
| 8 | 5 | UART1 RX | Master GPIO4(TX) | Serial RX |
| 40 | - | VBUS | Power | 5V |
| 39 | - | 3V3OUT | Power | 3.3V |

---

## I2C Bus Wiring (Physical Connections)

```
Master Pico               Stepper Pico              Actuator Pico
Pin 2 (GPIO0/SDA) ───┬─→ Pin 2 (GPIO0/SDA) ───┐
                     │                         │
Pin 3 (GPIO1/SCL) ───┼─→ Pin 3 (GPIO1/SCL) ───→ Pin 3 (GPIO1/SCL)
                     │                         │
Pin 1 (GND) ─────────┼─→ Pin 1 (GND) ─────────→ Pin 1 (GND)
                     │                 
                     └─[4.7kΩ]─[4.7kΩ]─ (pull-ups)
```

---

## UART Radar Connection (Physical Wires)

```
Master Pico              Radar Pico
Pin 7 (GPIO4/TX) ─────→ Pin 8 (GPIO5/RX)
Pin 8 (GPIO5/RX) ←───── Pin 7 (GPIO4/TX)
Pin 1 (GND) ────────────→ Pin 1 (GND)
```

---

## Motor Control Physical Connections

```
Stepper Pico                 Stepper Driver Module
Pin 8 (GPIO5/PUL) ─────────→ PUL+ input
Pin 10 (GPIO6/DIR) ────────→ DIR+ input
Pin 11 (GPIO7/ENA) ────────→ ENA+ input
Pin 1,6 or 9 (GND) ────────→ GND-
```

---

## Sensor Wiring (Physical)

**OMRON Inductive Sensor (LJ12A3-4Z/BY):**
```
Brown wire (6-36V) ─────→ External 5-24V power supply (+)
Blue wire (GND) ────────→ Common ground (Pico Pin 1)
Black wire (Signal) ────→ Stepper Pico Pin 31 (GPIO20)

Common ground between:
- Stepper Pico
- Master Pico
- Sensor
- Stepper driver
```

**Servo Power Connection:**
```
Red wire (5V) ──────────→ External 5V or Pin 40 (VBUS)
Brown/Black wire (GND) ──→ Pico Pin 1 or Pin 6 (GND)
Yellow wire (Signal) ────→ Actuator Pico Pin 4 (GPIO2)
```

---

## Power Distribution (Physical)

```
External 5V PSU
    │
    ├──→ Master Pico Pin 40 (VBUS)
    ├──→ Stepper Pico Pin 40 (VBUS)
    ├──→ Actuator Pico Pin 40 (VBUS)
    ├──→ Radar Pico Pin 40 (VBUS)
    ├──→ Stepper Motor Driver VCC
    ├──→ Servo Motor Power (Red wire)
    └──→ Sensor Power (Brown wire, 6-36V)

External GND
    │
    ├──→ All Picos Pin 1/6/9/12/15/18/21/24/27/30/33 (any GND)
    ├──→ Stepper Motor Driver GND
    ├──→ Servo Motor GND (Brown/Black wire)
    └──→ Sensor GND (Blue wire)
```

---

## Quick Reference - Critical Pins

| Function | Pico | Physical Pin | GPIO |
|----------|------|--------------|------|
| I2C Master SDA | Master | 2 | 0 |
| I2C Master SCL | Master | 3 | 1 |
| I2C Slave SDA | Stepper/Actuator | 2 | 0 |
| I2C Slave SCL | Stepper/Actuator | 3 | 1 |
| Stepper PUL | Stepper | 8 | 5 |
| Stepper DIR | Stepper | 10 | 6 |
| Stepper ENA | Stepper | 11 | 7 |
| Home Sensor | Stepper | 31 | 20 |
| Servo PWM | Actuator | 4 | 2 |
| UART0 TX (Pi 4) | Master | 25 | 16 |
| UART0 RX (Pi 4) | Master | 26 | 17 |
| UART1 TX (Radar) | Master | 7 | 4 |
| UART1 RX (Radar) | Master | 8 | 5 |
| GND (All) | All | 1,6,9,12,15,18,21,24,27,30,33 | - |
| 5V Power | Any | 40 | - |
| 3.3V Output | Any | 39 | - |

---

## Connection Checklist

### I2C Bus Setup (Critical)
- [ ] Master GPIO0 (SDA) connected to: Stepper GPIO0, Actuator GPIO0, GND side of pull-up
- [ ] Master GPIO1 (SCL) connected to: Stepper GPIO1, Actuator GPIO1, GND side of pull-up
- [ ] 4.7kΩ pull-up resistors on both SDA and SCL
- [ ] All ground connections common (Master GND = Stepper GND = Actuator GND)
- [ ] I2C addresses verified (Stepper 0x10, Actuator 0x12)

### UART Connections

**Pi 4 Server Connection (UART0):**
- [ ] Master GPIO16 to Pi 4 RX (TX to RX)
- [ ] Master GPIO17 to Pi 4 TX (RX to TX)
- [ ] Master GND to Pi 4 GND
- [ ] Baud Rate: 460800 bps

**Radar Connection (UART1):**
- [ ] Master GPIO4 to Radar GPIO5 (TX to RX)
- [ ] Master GPIO5 to Radar GPIO4 (RX to TX)
- [ ] Master GND to Radar GND
- [ ] Baud Rate: 115200 bps

### Motor Connections
- [ ] Stepper motor PUL/DIR/ENA wired to driver
- [ ] Home sensor (OMRON) wired: Brown=5V, Blue=GND, Black=GPIO20
- [ ] Stepper driver GND connected to Master/Stepper GND

### Servo Connections
- [ ] Servo PWM signal on GPIO2
- [ ] Servo power (Red=5V, Brown/Black=GND)
- [ ] Servo GND common with system GND

### Power Supply
- [ ] Master Pico VSYS connected to 5V supply
- [ ] All Picos share common GND
- [ ] 5V available for: Stepper motor (via driver), Servo (if high torque), Radar sensor
- [ ] 3.3V regulated output for sensor logic levels

---

## I2C Address Space

| Address | Hex | Device | Status |
|---------|-----|--------|--------|
| 0x08 | 7-bit addressing | Reserved | - |
| 0x10 | Stepper Motor | Active |
| 0x12 | Servo/Actuator | Active |
| 0x48 | Optional | Available |
| 0x68 | Optional | Available |
| 0x70 | Optional | Available |

---

## Troubleshooting

### I2C Not Working
1. Verify both SDA/SCL connected to GPIO0/1 on **all devices**
2. Check 4.7kΩ pull-up resistors present
3. Verify GND common between all devices
4. Test with `i2cdetect -y 1` command
5. Check I2C address matches (0x10 for stepper, 0x12 for actuator)

### Motor Not Responding
1. Check PUL/DIR/ENA wired to GPIO5/6/7
2. Verify stepper driver has power and correct GND
3. Test I2C commands with `GET position` (0x02 0x10)

### Servo Not Moving
1. Verify GPIO2 PWM output active
2. Check servo power (Red/Brown/Black wires)
3. Test with manual PWM pulse (1-2ms on 50Hz)

### Radar Data Not Received
1. Check UART1 TX/RX swapped (Master TX4→RX5, RX5→TX4)
2. Verify 115200 baud rate
3. Check Radar GND common with system GND
4. Monitor with serial terminal at 115200

---

## I2C Master Commands for Testing

```python
import smbus

bus = smbus.SMBus(1)

# Detect slaves on I2C bus
i2cdetect -y 1

# Get stepper position
data = [0x02, 0x10]  # GET position
bus.write_i2c_block_data(0x10, 0, data)
response = bus.read_i2c_block_data(0x10, 0, 3)
print(f"Position: {(response[1] << 8) | response[2]}°")

# Move stepper to 90°
data = [0x04, 0x01, 0x00, 0x5A]  # move to 90
bus.write_i2c_block_data(0x10, 0, data)
```

---

## UART Configuration Details

### UART0 (Pi 4 Server Communication)
- **Baud Rate:** 460800 bps (optimal for local GPIO connection)
- **Data Bits:** 8
- **Stop Bits:** 1
- **Parity:** None
- **Purpose:** High-speed bidirectional communication with Raspberry Pi 4
- **Secondary:** Debug output simultaneously available on same pins when not in active server comm

**Baud Rate Selection Rationale:**
- 115200: Too slow for high-bandwidth server communication
- 230400: Good but can cause processing lag on Pico under heavy I2C load
- **460800: Optimal** - Fast enough for real-time server commands without degrading Pico processing
- 921600: Marginal stability over GPIO connections, not recommended

**Local GPIO Connection Benefits:**
- Short distance (Pi 4 to Pico on same board/enclosure)
- Low noise environment
- Supports higher baud rates without errors
- 460800 provides ~54KB/s throughput (ideal for sensor data + commands)

### UART1 (Radar Sensor)
- **Baud Rate:** 115200 bps (radar sensor standard)
- **Data Bits:** 8
- **Stop Bits:** 1
- **Parity:** None

---

## Supported I2C Frequency

- Master Configuration: **100 kHz** (standard, most compatible)
- Max Supported: 400 kHz (fast mode)
- Typical for this system: 100 kHz (safe, reliable)

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2026-04-07 | Added Pi 4 server UART connection on UART0 (GPIO16/17) at 460800 baud; dual-purpose debug + server communication; updated architecture diagrams |
| 1.0 | 2026-04-04 | Initial pinout documentation |

