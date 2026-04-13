/**
 * Serial Communication Handler
 * Manages Python serial_bridge.py subprocess for UART communication to Pico Master
 * 
 * Two-way communication:
 * - Commands: Node.js → stdin → serial_bridge.py → Serial Port
 * - Responses: Serial Port → serial_bridge.py → stdout → Node.js
 */

const { spawn } = require('child_process');
const path = require('path');
const logger = require('./logger');

class SerialComm {
    constructor(options = {}) {
        this.pythonProcess = null;
        this.isConnected = false;
        this.isInitializing = false;
        
        // Pending command callbacks
        this.pendingCommands = new Map();
        this.commandTimeout = options.commandTimeout || 10000;
        
        // Serial data callbacks
        this.dataHandlers = [];
        
        // Configuration
        this.scriptPath = options.scriptPath || path.join(__dirname, '../serial_bridge.py');
        this.pythonExe = options.pythonExe || 'python3';
    }

    /**
     * Initialize serial bridge
     */
    async initialize() {
        return new Promise((resolve, reject) => {
            if (this.isInitializing) {
                return reject(new Error('Initialization already in progress'));
            }

            if (this.pythonProcess) {
                return reject(new Error('Serial bridge already initialized'));
            }

            this.isInitializing = true;

            try {
                logger.info(`[SERIAL] Spawning Python bridge: ${this.scriptPath}`);
                
                this.pythonProcess = spawn(this.pythonExe, [this.scriptPath], {
                    stdio: ['pipe', 'pipe', 'pipe'],
                    detached: false
                });

                // Handle stdout: both responses and serial data
                this.pythonProcess.stdout.on('data', (data) => {
                    this._handleStdout(data.toString());
                });

                // Handle stderr: logging from Python
                this.pythonProcess.stderr.on('data', (data) => {
                    data.toString().split('\n').forEach(line => {
                        if (line.trim()) {
                            logger.debug(`[SERIAL-PYTHON] ${line}`);
                        }
                    });
                });

                // Handle process exit
                this.pythonProcess.on('exit', (code) => {
                    logger.warn(`[SERIAL] Python process exited with code ${code}`);
                    this.pythonProcess = null;
                    this.isConnected = false;
                });

                // Handle process error
                this.pythonProcess.on('error', (err) => {
                    logger.error(`[SERIAL] Failed to spawn Python process: ${err.message}`);
                    this.pythonProcess = null;
                    this.isConnected = false;
                    this.isInitializing = false;
                    reject(err);
                });

                // Test connection with status command
                const statusTimeout = setTimeout(() => {
                    this.isInitializing = false;
                    reject(new Error('Serial bridge initialization timeout'));
                }, 5000);

                this.sendCommand({ action: 'status' }, (err, result) => {
                    clearTimeout(statusTimeout);
                    this.isInitializing = false;

                    if (err) {
                        logger.error(`[SERIAL] Status check failed: ${err.message}`);
                        reject(err);
                    } else {
                        this.isConnected = result.connected;
                        logger.info(`[SERIAL] Bridge initialized. Connected: ${this.isConnected}`);
                        resolve(result);
                    }
                });

            } catch (err) {
                this.isInitializing = false;
                logger.error(`[SERIAL] Initialization error: ${err.message}`);
                reject(err);
            }
        });
    }

    /**
     * Send command to serial device
     * @param {string} deviceCommand - Full command string (e.g., "stepper:status")
     * @param {number} timeout - Optional timeout override (ms)
     * @returns {Promise<object>} Response from device
     */
    async sendDeviceCommand(deviceCommand, timeout = null) {
        if (!this.pythonProcess) {
            throw new Error('Serial bridge not initialized');
        }

        return this._sendCommand(
            { action: 'send', command: deviceCommand },
            timeout || this.commandTimeout
        );
    }

    /**
     * Low-level command sending (internal use)
     * @private
     */
    async _sendCommand(command, timeout = null) {
        return new Promise((resolve, reject) => {
            if (!this.pythonProcess) {
                return reject(new Error('Serial bridge not connected'));
            }

            const cmdId = Math.random().toString(36);
            
            // Set timeout
            const timeoutHandle = setTimeout(() => {
                this.pendingCommands.delete(cmdId);
                reject(new Error(`Command timeout after ${timeout}ms`));
            }, timeout || this.commandTimeout);

            // Register pending command
            this.pendingCommands.set(cmdId, {
                timeout: timeoutHandle,
                resolve: (data) => {
                    clearTimeout(timeoutHandle);
                    resolve(data);
                },
                reject: (error) => {
                    clearTimeout(timeoutHandle);
                    reject(error);
                }
            });

            try {
                const message = JSON.stringify(command) + '\n';
                this.pythonProcess.stdin.write(message, (err) => {
                    if (err) {
                        this.pendingCommands.delete(cmdId);
                        clearTimeout(timeoutHandle);
                        logger.error(`[SERIAL] Failed to send command: ${err.message}`);
                        reject(err);
                    }
                });
            } catch (err) {
                this.pendingCommands.delete(cmdId);
                clearTimeout(timeoutHandle);
                reject(err);
            }
        });
    }

    /**
     * Register handler for serial data
     * @param {function} handler - Called with (data) when serial data arrives
     */
    onSerialData(handler) {
        if (typeof handler === 'function') {
            this.dataHandlers.push(handler);
        }
    }

    /**
     * Remove serial data handler
     */
    offSerialData(handler) {
        const idx = this.dataHandlers.indexOf(handler);
        if (idx > -1) {
            this.dataHandlers.splice(idx, 1);
        }
    }

    /**
     * Handle stdout from Python process
     * @private
     */
    _handleStdout(data) {
        const lines = data.toString().split('\n');
        
        for (const line of lines) {
            if (!line.trim()) continue;

            try {
                const message = JSON.parse(line);

                if (message.type === 'serial_data') {
                    // Serial data from device
                    logger.debug(`[SERIAL-DATA] ${message.data}`);
                    this.dataHandlers.forEach(handler => {
                        try {
                            handler(message.data);
                        } catch (err) {
                            logger.error(`[SERIAL] Error in data handler: ${err.message}`);
                        }
                    });

                } else if (message.type === 'command_response') {
                    // Response to our command - resolve first pending command
                    const pending = this.pendingCommands.values().next().value;
                    if (pending) {
                        this.pendingCommands.delete(
                            [...this.pendingCommands.keys()][0]
                        );
                        pending.resolve(message.data);
                    }

                } else if (message.type === 'error') {
                    logger.error(`[SERIAL] Python error: ${message.message}`);
                }
            } catch (err) {
                logger.warn(`[SERIAL] Failed to parse message: ${line}`);
            }
        }
    }

    /**
     * Send command (callback-based, for backward compatibility)
     * @private
     */
    sendCommand(command, callback) {
        this._sendCommand(command)
            .then(result => callback(null, result))
            .catch(err => callback(err, null));
    }

    /**
     * Disconnect from serial
     */
    async disconnect() {
        return new Promise((resolve) => {
            if (!this.pythonProcess) {
                return resolve();
            }

            try {
                this.pythonProcess.kill();
                this.pythonProcess = null;
                this.isConnected = false;
                logger.info('[SERIAL] Disconnected from serial bridge');
            } catch (err) {
                logger.error(`[SERIAL] Error disconnecting: ${err.message}`);
            }

            resolve();
        });
    }

    /**
     * Disconnect from serial (alias for disconnect)
     */
    async close() {
        return this.disconnect();
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            connected: this.isConnected,
            initialized: this.pythonProcess !== null,
            pendingCommands: this.pendingCommands.size
        };
    }
}

module.exports = SerialComm;
