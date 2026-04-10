/**
 * UART Serial Communication Module
 * Handles communication with Pico Master via /dev/ttyAMA0
 */

const logger = require('./logger');

// Check if we're on Raspberry Pi (UART device exists)
const fs = require('fs');
const isRaspberryPi = process.platform === 'linux' && fs.existsSync('/dev/ttyAMA0');

let SerialPort;
try {
    if (isRaspberryPi) {
        const sp = require('serialport');
        SerialPort = sp.SerialPort || sp;
        logger.debug(`[UART] SerialPort loaded: ${typeof SerialPort}`);
    } else {
        logger.warn('[UART] Not on Raspberry Pi - using mock UART mode');
        SerialPort = null;
    }
} catch (e) {
    logger.error(`[UART] Failed to load serialport: ${e.message}`);
    SerialPort = null;
}

let port = null;
let isOpening = false;
const PORT_PATH = process.env.SERIAL_PORT || '/dev/ttyAMA0';
const BAUD_RATE = Number(process.env.BAUD_RATE || 460800);
const TIMEOUT = 2000;
let pendingResolve = null;
let pendingReject = null;
let buffer = '';

async function initialize() {
    return new Promise((resolve, reject) => {
        // If not on Raspberry Pi, reject immediately
        if (!isRaspberryPi) {
            logger.warn('[UART] UART not available (not on Raspberry Pi)');
            return reject(new Error('UART not available on this platform'));
        }

        try {
            // If port is already trying to open, reject
            if (isOpening) {
                return reject(new Error('Port initialization already in progress'));
            }

            if (!SerialPort) {
                logger.warn('[UART] SerialPort library not available - UART disabled');
                return reject(new Error('SerialPort library not available'));
            }

            logger.info(`[UART] Opening ${PORT_PATH} at ${BAUD_RATE} baud`);

            // Clean up existing port
            if (port) {
                try {
                    port.removeAllListeners();
                    if (port.isOpen) {
                        port.close();
                    }
                } catch (e) {
                    // Ignore cleanup errors
                }
                port = null;
            }

            buffer = '';
            isOpening = true;

            // Create port with explicit settings
            let portInstance;
            try {
                portInstance = new SerialPort({
                    path: PORT_PATH,
                    baudRate: BAUD_RATE,
                    autoOpen: false
                });
            } catch (e) {
                isOpening = false;
                logger.error(`[UART] Failed to create port: ${e.message}`);
                return reject(e);
            }

            port = portInstance;

            // Setup data listener
            port.on('data', (data) => {
                buffer += data.toString();
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    const str = line.trim();
                    if (str && pendingResolve) {
                        logger.debug(`[UART-REC] ${str}`);
                        const fn = pendingResolve;
                        pendingResolve = null;
                        pendingReject = null;
                        fn(str);
                    }
                }
            });

            // Setup error listener
            const onPortError = (err) => {
                logger.error(`[UART] Port error: ${err.message}`);
                if (pendingReject) {
                    const fn = pendingReject;
                    pendingReject = null;
                    pendingResolve = null;
                    fn(err);
                }
            };
            port.on('error', onPortError);

            // Setup close listener
            port.on('close', () => {
                logger.warn('[UART] Port closed');
            });

            // Set a timeout for opening
            const openTimeout = setTimeout(() => {
                isOpening = false;
                if (port && !port.isOpen) {
                    reject(new Error('UART port open timeout'));
                }
            }, 5000);

            // Try to open the port
            try {
                if (typeof port.open === 'function') {
                    port.open((err) => {
                        clearTimeout(openTimeout);
                        isOpening = false;
                        
                        if (err) {
                            logger.error(`[UART] Failed to open port: ${err.message}`);
                            reject(err);
                        } else {
                            logger.info(`[UART] Connected to ${PORT_PATH} at ${BAUD_RATE} baud`);
                            resolve();
                        }
                    });
                } else {
                    // If port.open is not a function, port might already be opening
                    isOpening = false;
                    reject(new Error('port.open is not a function'));
                }
            } catch (e) {
                clearTimeout(openTimeout);
                isOpening = false;
                logger.error(`[UART] Exception calling port.open: ${e.message}`);
                reject(e);
            }

        } catch (err) {
            isOpening = false;
            logger.error(`[UART] Init error: ${err.message}`);
            reject(err);
        }
    });
}

function send(command) {
    return new Promise((resolve, reject) => {
        if (!port || !port.isOpen) {
            reject(new Error('UART port not open'));
            return;
        }

        if (!command.endsWith('\n')) {
            command += '\n';
        }

        const timeout = setTimeout(() => {
            pendingResolve = null;
            pendingReject = null;
            reject(new Error(`UART timeout (${TIMEOUT}ms)`));
        }, TIMEOUT);

        pendingResolve = (data) => {
            clearTimeout(timeout);
            resolve(data);
        };

        pendingReject = (err) => {
            clearTimeout(timeout);
            reject(err);
        };

        logger.debug(`[UART-SEND] ${command.trim()}`);
        port.write(command, (err) => {
            if (err) {
                clearTimeout(timeout);
                if (pendingReject) {
                    pendingReject(err);
                    pendingReject = null;
                }
            }
        });
    });
}

async function close() {
    return new Promise((resolve) => {
        if (port && port.isOpen) {
            port.close((err) => {
                if (err) logger.error(`[UART] Close error: ${err.message}`);
                else logger.info('[UART] Port closed');
                resolve();
            });
        } else {
            resolve();
        }
    });
}

module.exports = {
    initialize,
    send,
    close
};


