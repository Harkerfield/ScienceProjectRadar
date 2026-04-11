#!/usr/bin/env python3
"""
Serial Bridge - Connects Node.js to Raspberry Pi Pico via Serial Port
Uses threading to listen for serial data without blocking on stdin.

Architecture:
  stdin (from Node.js) → Command Handler → Serial Port → Pico Master
  Serial Port (from Pico) → Response Handler → stdout (to Node.js) → prefix: SERIAL_DATA:
  Logs → stderr (for debugging)
"""

import serial
import sys
import threading
import json
import time
import logging
from pathlib import Path

# Configure logging to stderr (stdout reserved for JSON communication to Node.js)
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Configuration
SERIAL_PORT = '/dev/ttyAMA0'           # Raspberry Pi UART port
BAUD_RATE = 460800                     # Pico Master UART0 speed
TIMEOUT = 2.0                          # Serial read timeout
COMMAND_TIMEOUT = 5000                 # Command response timeout (ms)

# Global state
ser = None
is_running = False
pending_commands = {}  # Track pending commands by ID
response_thread = None
command_id_counter = 0
lock = threading.Lock()


def connect_serial():
    """Establish serial connection to Pico Master"""
    global ser
    try:
        logger.info(f"Connecting to {SERIAL_PORT} at {BAUD_RATE} baud...")
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)
        time.sleep(0.5)  # Let port settle
        logger.info("Serial connection established")
        return True
    except serial.SerialException as e:
        logger.error(f"Failed to connect to serial: {e}")
        return False


def listen_to_serial():
    """Background thread: Continuously read from serial and send to Node.js"""
    global is_running
    
    buffer = ''
    logger.info("Serial listener thread started")
    
    while is_running and ser:
        try:
            if ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer += data.decode('utf-8', errors='replace')
                
                # Process complete lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    
                    if line:
                        # Send to Node.js with SERIAL_DATA prefix
                        response = {'type': 'serial_data', 'data': line}
                        print(json.dumps(response))
                        sys.stdout.flush()
                        logger.debug(f"Sent to Node.js: {line}")
            else:
                time.sleep(0.01)  # Prevent CPU spinning
                
        except Exception as e:
            logger.error(f"Error in serial listener: {e}")
            time.sleep(0.1)


def send_to_serial(command):
    """Send command to serial device"""
    try:
        if not ser or not ser.is_open:
            return False
        
        # Ensure command ends with newline
        if not command.endswith('\n'):
            command += '\n'
        
        ser.write(command.encode('utf-8'))
        ser.flush()
        logger.debug(f"Sent to serial: {command.strip()}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending to serial: {e}")
        return False


def handle_command(cmd_data):
    """Process incoming command from Node.js"""
    try:
        action = cmd_data.get('action')
        
        if action == 'connect':
            result = connect_serial()
            return {'status': 'ok' if result else 'error', 'connected': result}
        
        elif action == 'disconnect':
            if ser and ser.is_open:
                ser.close()
                return {'status': 'ok', 'message': 'Disconnected'}
            return {'status': 'ok', 'message': 'Not connected'}
        
        elif action == 'status':
            return {
                'status': 'ok',
                'connected': ser is not None and ser.is_open,
                'port': SERIAL_PORT,
                'baudrate': BAUD_RATE
            }
        
        elif action == 'send':
            command = cmd_data.get('command')
            if not command:
                return {'status': 'error', 'message': 'No command provided'}
            
            success = send_to_serial(command)
            return {
                'status': 'ok' if success else 'error',
                'command': command,
                'sent': success
            }
        
        else:
            return {'status': 'error', 'message': f'Unknown action: {action}'}
    
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        return {'status': 'error', 'message': str(e)}


def main():
    """Main loop: Listen for commands from Node.js via stdin"""
    global is_running, response_thread
    
    logger.info("Serial bridge started")
    logger.info("Waiting for commands from Node.js...")
    
    try:
        # Connect to serial device
        if not connect_serial():
            logger.warning("Could not connect to serial (will retry on first command)")
        
        # Start serial listener thread
        is_running = True
        response_thread = threading.Thread(target=listen_to_serial, daemon=True)
        response_thread.start()
        logger.info("Serial listener thread spawned")
        
        # Main loop: Read commands from Node.js
        for line in sys.stdin:
            try:
                cmd_data = json.loads(line.strip())
                result = handle_command(cmd_data)
                
                # Send response back to Node.js as JSON
                response = {'type': 'command_response', 'data': result}
                print(json.dumps(response))
                sys.stdout.flush()
                
                logger.debug(f"Command processed: {cmd_data.get('action')}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                response = {'type': 'error', 'message': f'Invalid JSON: {e}'}
                print(json.dumps(response))
                sys.stdout.flush()
            
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt in main loop")
    
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
    
    finally:
        is_running = False
        if ser and ser.is_open:
            try:
                ser.close()
                logger.info("Serial port closed")
            except:
                pass
        logger.info("Serial bridge stopped")


if __name__ == '__main__':
    main()
