/**
 * UART Serial Communication Module
 * Handles communication with Pico Master via /dev/ttyAMA0
 */

const SerialPort = require('serialport');
const logger = require('./logger');

class UARTSerial {
    constructor() {
        this.port = null;
        this.isOpen = false;
        this.PORT_PATH = '/dev/ttyAMA0';
        this.BAUD_RATE = 460800;
        this.TIMEOUT = 2000; // 2 second timeout per command
    }

    async initialize() {
        return new Promise((resolve, reject) => {
            try {
                this.port = new SerialPort.SerialPort({
                    path: this.PORT_PATH,
                    baudRate: this.BAUD_RATE,
                    autoOpen: false
                });

                this.port.on('error', (err) => {
                    logger.error(`[UART] Port error: ${err.message}`);
                    this.isOpen = false;
                });

                this.port.on('close', () => {
                    logger.warn('[UART] Port closed');
                    this.isOpen = false;
                });

                this.port.open((err) => {
                    if (err) {
                        logger.error(`[UART] Failed to open port: ${err.message}`);
                        this.isOpen = false;
                        reject(err);
                    } else {
                        this.isOpen = true;
                        logger.info(`[UART] Connected to ${this.PORT_PATH} at ${this.BAUD_RATE} baud`);
                        resolve();
                    }
                });
            } catch (err) {
                logger.error(`[UART] Initialize error: ${err.message}`);
                reject(err);
            }
        });
    }

    send(command) {
        return new Promise((resolve, reject) => {
            if (!this.isOpen) {
                reject(new Error('UART port is not open'));
                return;
            }

            if (!command.endsWith('\n')) {
                command += '\n';
            }

            let responseBuffer = '';
            const timeout = setTimeout(() => {
                this.port.removeListener('data', dataHandler);
                reject(new Error(`UART timeout waiting for response (${this.TIMEOUT}ms)`));
            }, this.TIMEOUT);

            const dataHandler = (data) => {
                responseBuffer += data.toString('utf-8', errors = 'replace');

                // Check if we got a complete response (ends with newline)
                if (responseBuffer.includes('\n')) {
                    clearTimeout(timeout);
                    this.port.removeListener('data', dataHandler);
                    
                    // Split in case multiple messages arrived
                    const lines = responseBuffer.split('\n');
                    const response = lines[0].trim();
                    
                    if (response) {
                        resolve(response);
                    } else if (lines[1]) {
                        resolve(lines[1].trim());
                    } else {
                        reject(new Error('Empty response from Pico'));
                    }
                }
            };

            try {
                logger.debug(`[UART-SEND] ${command.trim()}`);
                this.port.write(command.encode ? command : Buffer.from(command));
                this.port.on('data', dataHandler);
            } catch (err) {
                clearTimeout(timeout);
                reject(err);
            }
        });
    }

    async close() {
        return new Promise((resolve) => {
            if (this.port && this.isOpen) {
                this.port.close(() => {
                    this.isOpen = false;
                    logger.info('[UART] Port closed');
                    resolve();
                });
            } else {
                resolve();
            }
        });
    }
}

module.exports = UARTSerial;
