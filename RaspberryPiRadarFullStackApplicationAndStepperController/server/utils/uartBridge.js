/**
 * Python UART Bridge - Spawns Python child process for UART communication
 * Replaces problematic serialport library with proven Python implementation
 */

const { spawn } = require('child_process');
const path = require('path');
const logger = require('./logger');

let pythonProcess = null;
let commandQueue = [];
let pendingCallbacks = new Map();
let messageId = 0;
let isConnected = false;

async function initialize() {
    return new Promise((resolve, reject) => {
        if (pythonProcess) {
            logger.warn('[UART-BRIDGE] Python process already running');
            return reject(new Error('Python bridge already initialized'));
        }

        try {
            // Spawn Python process
            const pythonScriptPath = path.join(__dirname, '../uart_controller.py');
            logger.info(`[UART-BRIDGE] Spawning Python process: ${pythonScriptPath}`);

            pythonProcess = spawn('python3', [pythonScriptPath], {
                stdio: ['pipe', 'pipe', 'pipe'],
                detached: false
            });

            let initOutput = '';
            let pythonReady = false;

            // Handle stdout (JSON responses from Python)
            pythonProcess.stdout.on('data', (data) => {
                const lines = data.toString().split('\n');
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        const response = JSON.parse(line);
                        
                        // If this is a pending callback response
                        if (response._id !== undefined && pendingCallbacks.has(response._id)) {
                            const callback = pendingCallbacks.get(response._id);
                            pendingCallbacks.delete(response._id);
                            callback(null, response);
                        }
                    } catch (e) {
                        logger.warn(`[UART-BRIDGE] Failed to parse JSON: ${line}`);
                    }
                }
            });

            // Handle stderr (logging from Python)
            pythonProcess.stderr.on('data', (data) => {
                const lines = data.toString().split('\n');
                for (const line of lines) {
                    if (line.trim()) {
                        logger.debug(`[UART-PYTHON] ${line}`);
                    }
                }
            });

            // Handle process exit
            pythonProcess.on('exit', (code) => {
                logger.warn(`[UART-BRIDGE] Python process exited with code ${code}`);
                pythonProcess = null;
                isConnected = false;
            });

            // Handle process errors
            pythonProcess.on('error', (err) => {
                logger.error(`[UART-BRIDGE] Failed to spawn Python process: ${err.message}`);
                pythonProcess = null;
                isConnected = false;
                reject(err);
            });

            // Send status command to verify Python is ready
            const timeout = setTimeout(() => {
                reject(new Error('Python bridge initialization timeout'));
            }, 5000);

            sendCommand({ action: 'status' }, (err, result) => {
                clearTimeout(timeout);
                
                if (err) {
                    logger.error(`[UART-BRIDGE] Status check failed: ${err.message}`);
                    reject(err);
                } else {
                    isConnected = result.connected;
                    logger.info(`[UART-BRIDGE] Python bridge initialized. UART connected: ${isConnected}`);
                    resolve();
                }
            });

        } catch (err) {
            logger.error(`[UART-BRIDGE] Initialization error: ${err.message}`);
            reject(err);
        }
    });
}

function sendCommand(command, callback) {
    if (!pythonProcess) {
        logger.warn('[UART-BRIDGE] Python process not running');
        if (callback) {
            callback(new Error('Python bridge not initialized'));
        }
        return;
    }

    try {
        // Add message ID for tracking response
        const msgId = messageId++;
        command._id = msgId;

        // Register callback for this message
        if (callback) {
            pendingCallbacks.set(msgId, callback);
            
            // 10 second timeout for responses
            setTimeout(() => {
                if (pendingCallbacks.has(msgId)) {
                    pendingCallbacks.delete(msgId);
                    logger.warn(`[UART-BRIDGE] Command timeout: ${command.action}`);
                    callback(new Error('Command timeout'));
                }
            }, 10000);
        }

        // Send command as JSON to Python
        pythonProcess.stdin.write(JSON.stringify(command) + '\n');

    } catch (err) {
        logger.error(`[UART-BRIDGE] Error sending command: ${err.message}`);
        if (callback) {
            callback(err);
        }
    }
}

async function send(command) {
    return new Promise((resolve, reject) => {
        sendCommand({ action: 'send', command: command }, (err, result) => {
            if (err) {
                reject(err);
            } else if (result.status !== 'ok') {
                reject(new Error(result.message || 'Unknown error'));
            } else {
                resolve(result.data);
            }
        });
    });
}

async function close() {
    return new Promise((resolve) => {
        if (pythonProcess) {
            pythonProcess.kill();
            pythonProcess = null;
            isConnected = false;
            logger.info('[UART-BRIDGE] Python process terminated');
        }
        resolve();
    });
}

function getStatus() {
    return {
        initialized: pythonProcess !== null,
        connected: isConnected
    };
}

module.exports = {
    initialize,
    send,
    close,
    getStatus
};
