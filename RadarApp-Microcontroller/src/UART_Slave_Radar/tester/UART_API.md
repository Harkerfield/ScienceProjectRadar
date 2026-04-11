# UART Radar Slave API Documentation

## Overview
The uart_Slave_Radar module provides UART communication interface for a radar sensor. The slave device continuously transmits radar readings and accepts USB commands to update or query sensor values using standardized JSON format.

## Device Information
- **Module:** uart_Slave_Radar
- **Protocol:** UART (Universal Asynchronous Receiver-Transmitter)
- **Slave Identifier:** 0x20 (virtual address, UART has no addressing)
- **Baud Rate:** 115200 (115.2 kbps)
- **Data Format:** JSON (UTF-8 encoded, newline terminated)
- **Communication Type:** Continuous stream + command/response on USB

## Hardware Configuration
- **UART Port:** UART(1)
- **TX Pin:** GPIO 4 (Data to Master)
- **RX Pin:** GPIO 5 (Data from Master)
- **Frequency:** 100ms per transmission cycle

---

## Continuous Output (UART)

The radar automatically sends sensor readings every 100ms:

```json
{"s":"ok","range":123,"vel":4.5}
```

### Output Fields
| Field | Type | Description | Range |
|-------|------|-------------|-------|
| `s` | string | Status ("ok" or "error") | - |
| `range` | integer | Distance reading | 0-400 cm |
| `vel` | float | Velocity reading (Doppler) | -20.0 to +20.0 m/s |

### Data Reception Example (Python)
```python
import serial

# Open serial connection to radar
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

while True:
    line = ser.readline().decode().strip()
    if line:
        # Parse JSON
        import json
        data = json.loads(line)
        print(f"Range: {data['range']}cm, Velocity: {data['vel']}m/s")
```

---

## USB Commands (Debugging/Control)

Send commands via USB serial to control the radar or query status. Available through the same USB port that shows debug output.

### Command Reference

#### READ - Get Current Sensor Values
**Command:** `READ`  
**Response:** `{"s":"ok","range":123,"vel":4.5}`  
**Description:** Returns current sensor readings

```python
ser.write(b'READ\n')
response = ser.readline().decode()
print(response)  # {"s":"ok","range":123,"vel":4.5}
```

---

#### STATUS - System Status Check
**Command:** `STATUS`  
**Response:** `{"s":"ok","msg":"operational","range":123,"vel":4.5}`  
**Description:** Verifies radar is operational

```python
ser.write(b'STATUS\n')
response = ser.readline().decode()
# Output: {"s":"ok","msg":"operational","range":123,"vel":4.5}
```

---

#### RANGE:<value> - Set Range Reading
**Command:** `RANGE:100`  
**Response:** `{"s":"ok","msg":"range_set","range":100,"vel":4.5}`  
**Description:** Simulate setting range to specified value (in cm)

```python
ser.write(b'RANGE:200\n')
response = ser.readline().decode()
# Output: {"s":"ok","msg":"range_set","range":200,"vel":4.5}
```

---

#### VEL:<value> - Set Velocity Reading
**Command:** `VEL:5.2`  
**Response:** `{"s":"ok","msg":"vel_set","range":123,"vel":5.2}`  
**Description:** Simulate setting velocity to specified value (in m/s)

```python
ser.write(b'VEL:8.5\n')
response = ser.readline().decode()
# Output: {"s":"ok","msg":"vel_set","range":123,"vel":8.5}
```

---

#### PING - Verify Online Status
**Command:** `PING`  
**Response:** `{"s":"ok","msg":"alive","addr":"0x20"}`  
**Description:** Confirms radar slave is responsive

```python
ser.write(b'PING\n')
response = ser.readline().decode()
# Output: {"s":"ok","msg":"alive","addr":"0x20"}
```

---

#### HELP - Show Available Commands
**Command:** `HELP`  
**Response:** Command list as text  
**Description:** Displays all available commands

```python
ser.write(b'HELP\n')
response = ser.readline().decode()
# Output: Commands: RANGE:<cm>|VEL:<m/s>|READ|STATUS|PING|HELP
```

---

## Response Format

### Success Response
```json
{"s":"ok","range":<int>,"vel":<float>}
```

### Success with Message
```json
{"s":"ok","msg":"<message>","range":<int>,"vel":<float>}
```

### Error Response
```json
{"s":"error","msg":"<error_code>"}
```

### Common Error Messages
- `unknown_command` - Command not recognized
- `command_error` - Error during execution
- `invalid_format` - Command format incorrect

---

## Communication Protocol

### Continuous Output Flow
```
Slave: (every 100ms) → {"s":"ok","range":123,"vel":4.5}\n
Slave: (every 100ms) → {"s":"ok","range":124,"vel":4.4}\n
Slave: (every 100ms) → {"s":"ok","range":120,"vel":4.6}\n
```

### Request-Response Flow (USB)
```
Master: (sends) → READ\n
Slave:  (receives command)
Slave:  (processes)
Slave:  (sends response) → {"s":"ok","range":123,"vel":4.5}\n
```

---

## Python Master Example Code

### Complete Radar Reader (UART + USB)

```python
import serial
import json
import threading
import time

class RadarController:
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        """
        Initialize UART connection to radar
        
        Args:
            port: Serial port (e.g., '/dev/ttyUSB0', 'COM3')
            baudrate: Baud rate (default 115200)
        """
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.latest_data = {"range": 0, "vel": 0.0}
        self.running = True
        
        # Start continuous reader thread
        self.reader_thread = threading.Thread(target=self._read_continuous, daemon=True)
        self.reader_thread.start()
    
    def _read_continuous(self):
        """Background thread: read continuous UART output"""
        while self.running:
            try:
                line = self.ser.readline().decode().strip()
                if line:
                    # Only capture data responses (skip command echoes)
                    if line.startswith('{"s":"ok","range"'):
                        data = json.loads(line)
                        self.latest_data = data
            except Exception as e:
                print(f"Read error: {e}")
            time.sleep(0.01)
    
    def parse_json_response(self, data_str):
        """Parse JSON response from radar"""
        try:
            return json.loads(data_str)
        except:
            # Fallback parser without json library
            result = {}
            data_str = data_str.strip('{}').split(',')
            for item in data_str:
                if ':' in item:
                    key, val = item.split(':', 1)
                    key = key.strip('"\'')
                    val = val.strip('"\'')
                    try:
                        result[key] = int(val) if val.isdigit() else float(val) if '.' in val else val
                    except:
                        result[key] = val
            return result
    
    def send_command(self, command):
        """
        Send USB command to radar
        
        Args:
            command: Command string (e.g., "READ", "STATUS")
            
        Returns:
            Parsed JSON response as dict
        """
        try:
            self.ser.write(command.encode() + b'\n')
            time.sleep(0.1)  # Wait for response
            
            # Clear input buffer to get latest response
            while self.ser.in_waiting:
                response_line = self.ser.readline().decode().strip()
            
            return self.parse_json_response(response_line)
        except Exception as e:
            print(f"Send error: {e}")
            return {"s": "error", "msg": "communication_error"}
    
    def get_latest_reading(self):
        """Get most recent radar reading from continuous stream"""
        return self.latest_data.copy()
    
    def read_status(self):
        """Request status via USB command"""
        response = self.send_command("STATUS")
        if response.get("s") == "ok":
            range_val = response.get("range", "?")
            vel_val = response.get("vel", "?")
            print(f"✓ Radar operational: Range={range_val}cm, Velocity={vel_val}m/s")
            return True
        else:
            print(f"✗ Error: {response.get('msg')}")
            return False
    
    def set_range(self, range_cm):
        """Set range reading (for testing)"""
        response = self.send_command(f"RANGE:{range_cm}")
        if response.get("s") == "ok":
            print(f"✓ Range set to {range_cm}cm")
            return True
        else:
            print(f"✗ Error: {response.get('msg')}")
            return False
    
    def set_velocity(self, vel_ms):
        """Set velocity reading (for testing)"""
        response = self.send_command(f"VEL:{vel_ms}")
        if response.get("s") == "ok":
            print(f"✓ Velocity set to {vel_ms}m/s")
            return True
        else:
            print(f"✗ Error: {response.get('msg')}")
            return False
    
    def ping(self):
        """Check if radar is online"""
        response = self.send_command("PING")
        if response.get("s") == "ok":
            print(f"✓ Radar is online ({response.get('addr')})")
            return True
        else:
            print(f"✗ Radar offline")
            return False
    
    def close(self):
        """Close serial connection"""
        self.running = False
        time.sleep(0.1)
        self.ser.close()

# Usage example
if __name__ == "__main__":
    # Create radar controller
    radar = RadarController(port='/dev/ttyUSB0')
    
    # Check online
    radar.ping()
    
    # Set test values
    radar.set_range(150)
    radar.set_velocity(5.5)
    
    # Check status
    radar.read_status()
    
    # Monitor continuous readings
    print("\nMonitoring continuous output (10 samples):")
    for i in range(10):
        data = radar.get_latest_reading()
        print(f"Sample {i+1}: Range={data['range']}cm, Velocity={data['vel']}m/s")
        time.sleep(0.2)
    
    # Close connection
    radar.close()
```

---

## UART to USB Bridge

The radar connects to the Master Pico via:

```
Radar Pico (UART1)
    ↓
Master Pico (UART receiver)
    ↓
USB Serial (to PC)
```

This allows real-time monitoring and debugging via standard serial tools like `minicom`:

```bash
minicom -D /dev/ttyUSB0 -b 115200
```

---

## Integration with Master API

The main I2C/UART Master API can receive radar data through:

1. **UART Direct:** Read from UART1 on Master Pico
2. **Parsed Response:** Decode JSON and integrate into system data

Example integration:
```python
def receive_radar_data():
    """Read from radar UART on Master Pico"""
    line = uart_input.readline().decode().strip()
    if line and line.startswith('{"s":"ok"'):
        return parse_json_line(line)
    return None
```

---

*Last Updated: April 7, 2026*  
*API Version: 1.0 (JSON Format)*
