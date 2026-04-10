#!/usr/bin/env python3
"""
UART Controller Bridge - Connects Node.js web server to Pico Master via Python
Runs as a child process, communicates with Node via JSON on stdin/stdout

This leverages proven Python UART functionality instead of problematic Node.js serialport
"""

import sys
import json
import serial
import time
import logging
from pathlib import Path

# Configure logging to stderr (stdout is reserved for JSON communication)
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Configuration
UART_PORT = '/dev/ttyAMA0'
BAUD_RATE = 460800
TIMEOUT = 2.0
MAX_RETRIES = 3

class UARTController:
    def __init__(self):
        self.port = None
        self.connected = False
        self.buffer = ''
        
    def connect(self):
        """Open connection to Pico Master"""
        if self.connected:
            return {'status': 'ok', 'message': 'Already connected'}
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Connecting to {UART_PORT} at {BAUD_RATE} baud (attempt {attempt + 1})...")
                self.port = serial.Serial(UART_PORT, BAUD_RATE, timeout=TIMEOUT)
                time.sleep(0.5)  # Let port settle
                self.connected = True
                logger.info(f"Connected to {UART_PORT}")
                return {'status': 'ok', 'message': f'Connected to {UART_PORT}'}
            except serial.SerialException as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)
        
        return {'status': 'error', 'message': f'Failed to connect after {MAX_RETRIES} attempts'}
    
    def disconnect(self):
        """Close connection to Pico Master"""
        if self.port:
            try:
                self.port.close()
                self.connected = False
                logger.info("Disconnected from UART")
                return {'status': 'ok', 'message': 'Disconnected'}
            except Exception as e:
                logger.error(f"Error disconnecting: {e}")
                return {'status': 'error', 'message': str(e)}
        return {'status': 'ok', 'message': 'Not connected'}
    
    def send_command(self, command):
        """
        Send command to Pico Master and receive response
        
        Command format: "DEVICE:COMMAND" or "DEVICE:COMMAND:ARGS"
        Response format: "DEVICE:STATUS[:DATA]"
        """
        if not self.connected:
            return {'status': 'error', 'message': 'Not connected to UART'}
        
        try:
            # Ensure command ends with newline
            if not command.endswith('\n'):
                command += '\n'
            
            logger.debug(f"Sending: {command.strip()}")
            self.port.write(command.encode())
            self.port.flush()
            
            # Read response until newline or timeout
            response = ''
            start_time = time.time()
            
            while time.time() - start_time < TIMEOUT:
                if self.port.in_waiting:
                    char = self.port.read(1).decode()
                    if char == '\n':
                        if response:
                            logger.debug(f"Received: {response}")
                            return {
                                'status': 'ok',
                                'data': response.strip(),
                                'raw': response.strip()
                            }
                    else:
                        response += char
                time.sleep(0.01)
            
            logger.warning(f"Timeout waiting for response to: {command.strip()}")
            return {'status': 'timeout', 'message': f'No response after {TIMEOUT}s'}
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            self.connected = False
            return {'status': 'error', 'message': str(e)}
    
    def check_status(self):
        """Get connection status"""
        return {
            'status': 'ok',
            'connected': self.connected,
            'port': UART_PORT,
            'baudrate': BAUD_RATE
        }

def handle_command(controller, cmd_data):
    """Handle incoming command from Node.js"""
    try:
        action = cmd_data.get('action')
        
        if action == 'connect':
            return controller.connect()
        
        elif action == 'disconnect':
            return controller.disconnect()
        
        elif action == 'status':
            return controller.check_status()
        
        elif action == 'send':
            command = cmd_data.get('command')
            if not command:
                return {'status': 'error', 'message': 'No command provided'}
            return controller.send_command(command)
        
        else:
            return {'status': 'error', 'message': f'Unknown action: {action}'}
    
    except Exception as e:
        logger.error(f"Error handling command: {e}")
        return {'status': 'error', 'message': str(e)}

def main():
    """Main loop - read commands from stdin, send responses to stdout"""
    controller = UARTController()
    logger.info("UART Controller bridge started")
    
    # Auto-connect on startup
    conn_result = controller.connect()
    logger.info(f"Auto-connect result: {conn_result}")
    
    try:
        while True:
            # Read JSON command from stdin
            try:
                line = sys.stdin.readline()
                if not line:
                    break  # EOF
                
                cmd_data = json.loads(line.strip())
                result = handle_command(controller, cmd_data)
                
                # Send JSON response to stdout
                sys.stdout.write(json.dumps(result) + '\n')
                sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")
                response = {'status': 'error', 'message': f'Invalid JSON: {e}'}
                sys.stdout.write(json.dumps(response) + '\n')
                sys.stdout.flush()
            
            except KeyboardInterrupt:
                break
    
    finally:
        controller.disconnect()
        logger.info("UART Controller bridge stopped")

if __name__ == '__main__':
    main()
