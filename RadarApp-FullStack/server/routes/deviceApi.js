const express = require('express');
const logger = require('../utils/logger');
const { validateDeviceCommand, formatDeviceCommand, getAvailableCommands, getDeviceInfo } = require('../utils/deviceCommandValidator');

/**
 * Create unified device API routes
 * All device interactions go through a single validation and execution pipeline
 * 
 * POST /api/device/:device/:command - Send command to device
 * GET /api/device/:device/info - Get available commands for device
 * GET /api/device/commands - Get all available commands
 */
function createUnifiedDeviceRoutes(serialComm, logger) {
    const router = express.Router();

    /**
     * GET /api/device
     * Device API discovery - shows available devices and endpoints
     */
    router.get('/', (req, res) => {
        try {
            const commands = getAvailableCommands();
            const devices = Object.keys(commands);
            
            res.json({
                success: true,
                message: 'Device Control API',
                availableDevices: devices,
                endpoints: {
                    'GET /api/device': 'This page - list available devices',
                    'GET /api/device/:device': 'Show available commands for a device',
                    'GET /api/device/:device/info': 'Detailed command info',
                    'POST /api/device/:device/:command': 'Execute a command',
                    'GET /api/device/commands': 'List all commands for all devices'
                },
                devices: devices.map(device => ({
                    name: device,
                    discovery: `/api/device/${device}`,
                    detailedInfo: `/api/device/${device}/info`
                })),
                examples: {
                    stepper: {
                        discoverCommands: '/api/device/STEPPER',
                        getStatus: '/api/device/STEPPER/STATUS',
                        spin: {
                            method: 'POST',
                            url: '/api/device/STEPPER/SPIN',
                            body: { args: { speed_us: 1500 } }
                        }
                    },
                    radar: {
                        discoverCommands: '/api/device/RADAR',
                        getStatus: '/api/device/RADAR/STATUS',
                        read: 'POST /api/device/RADAR/READ'
                    },
                    servo: {
                        discoverCommands: '/api/device/SERVO',
                        open: 'POST /api/device/SERVO/OPEN',
                        close: 'POST /api/device/SERVO/CLOSE'
                    }
                }
            });
        } catch (error) {
            logger.error(`Error fetching device list: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'SERVER_ERROR'
            });
        }
    });

    /**
     * GET /api/device/commands
     * Returns all available device commands and their parameters
     */
    router.get('/commands', (req, res) => {
        try {
            const commands = getAvailableCommands();
            res.json({
                success: true,
                data: commands
            });
        } catch (error) {
            logger.error(`Error fetching device commands: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'SERVER_ERROR'
            });
        }
    });

    /**
     * GET /api/device/:device
     * Show available commands for this device
     */
    router.get('/:device', (req, res) => {
        try {
            const { device } = req.params;
            const info = getDeviceInfo(device);
            
            if (info.error) {
                return res.status(404).json({
                    success: false,
                    error: info.error,
                    code: 'UNKNOWN_DEVICE'
                });
            }

            res.json({
                success: true,
                device: device,
                message: `Available commands for ${device}`,
                availableCommands: Object.keys(info.commands || {}),
                commands: info,
                endpoints: {
                    'GET /api/device/:device/:command': 'Send read-only command',
                    'POST /api/device/:device/:command': 'Send command with arguments',
                    'GET /api/device/:device/info': 'Detailed command specifications'
                }
            });
        } catch (error) {
            logger.error(`Error fetching device list: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'SERVER_ERROR'
            });
        }
    });

    /**
     * GET /api/device/:device/info
     * Returns available commands for specific device
     */
    router.get('/:device/info', (req, res) => {
        try {
            const { device } = req.params;
            const info = getDeviceInfo(device);
            
            if (info.error) {
                return res.status(404).json({
                    success: false,
                    error: info.error,
                    code: 'UNKNOWN_DEVICE'
                });
            }

            res.json({
                success: true,
                data: info
            });
        } catch (error) {
            logger.error(`Error fetching device info: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'SERVER_ERROR'
            });
        }
    });

    /**
     * POST /api/device/:device/:command
     * Send command to device with optional arguments
     * 
     * Body: { args: { key1: value1, key2: value2 } }
     */
    router.post('/:device/:command', async (req, res) => {
        try {
            const { device, command } = req.params;
            const args = req.body?.args || {};

            // Validate command
            const validation = validateDeviceCommand(device, command, args);
            if (!validation.valid) {
                logger.warn(`Invalid device command: ${device}:${command} - ${validation.error}`);
                return res.status(400).json({
                    success: false,
                    error: validation.error,
                    code: 'INVALID_COMMAND'
                });
            }

            // Format and send command through SerialComm
            const fullCommand = formatDeviceCommand(device, command, args);
            logger.info(`Executing device command: ${fullCommand}`);

            const response = await serialComm.sendDeviceCommand(fullCommand);
            
            res.json({
                success: true,
                command: fullCommand,
                response: response,
                data: response
            });

        } catch (error) {
            logger.error(`Error executing device command: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'EXECUTION_ERROR'
            });
        }
    });

    /**
     * GET /api/device/:device/:command
     * Alternative to POST for read-only commands (STATUS)
     */
    router.get('/:device/:command', async (req, res) => {
        try {
            const { device, command } = req.params;
            
            // Only allow read-only commands via GET
            const readOnlyCommands = ['STATUS', 'INFO', 'HEARTBEAT', 'ENABLE', 'INFO'];
            if (!readOnlyCommands.includes(command.toUpperCase())) {
                return res.status(405).json({
                    success: false,
                    error: `Command ${command} must use POST method`,
                    code: 'METHOD_NOT_ALLOWED'
                });
            }

            // Validate command
            const validation = validateDeviceCommand(device, command);
            if (!validation.valid) {
                logger.warn(`Invalid device command: ${device}:${command} - ${validation.error}`);
                return res.status(400).json({
                    success: false,
                    error: validation.error,
                    code: 'INVALID_COMMAND'
                });
            }

            // Format and send command
            const fullCommand = formatDeviceCommand(device, command);
            logger.debug(`Executing device command (GET): ${fullCommand}`);

            const response = await serialComm.sendDeviceCommand(fullCommand);
            
            res.json({
                success: true,
                command: fullCommand,
                response: response,
                data: response
            });

        } catch (error) {
            logger.error(`Error executing device command: ${error.message}`);
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'EXECUTION_ERROR'
            });
        }
    });

    return router;
}

module.exports = createUnifiedDeviceRoutes;
