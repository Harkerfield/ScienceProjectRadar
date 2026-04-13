const logger = require('../utils/logger');
const deviceCommands = require('../config/deviceCommands.json');

/**
 * Validate if a device command is valid
 * @param {string} device - Device name (stepper, RADAR, servo) - case-insensitive
 * @param {string} command - Command name (status, START, etc) - case-insensitive
 * @param {any} args - Command arguments
 * @returns {object} { valid: boolean, error?: string, device?: string, command?: string }
 */
function validateDeviceCommand(device, command, args) {
    // Normalize device and command to uppercase for case-insensitive lookup
    const normalizedDevice = device.toUpperCase();
    const normalizedCommand = command.toUpperCase();

    // Check if device exists
    if (!deviceCommands[normalizedDevice]) {
        return { valid: false, error: `Unknown device: ${device}` };
    }

    // Check if command exists for device
    if (!deviceCommands[normalizedDevice][normalizedCommand]) {
        const available = Object.keys(deviceCommands[normalizedDevice]).join(', ');
        return { valid: false, error: `Unknown command for ${device}: ${command}. Available: ${available}` };
    }

    const cmdDef = deviceCommands[normalizedDevice][normalizedCommand];
    
    // Validate arguments if specified
    if (cmdDef.args && args && typeof args === 'object') {
        for (const argName of cmdDef.args) {
            if (!(argName in args)) {
                return { valid: false, error: `Missing required argument: ${argName}` };
            }
        }

        // Validate enum values if specified
        if (cmdDef.validValues) {
            for (const [argName, validValues] of Object.entries(cmdDef.validValues)) {
                if (args[argName] && !validValues.includes(args[argName])) {
                    return { 
                        valid: false, 
                        error: `Invalid value for ${argName}: ${args[argName]}. Valid values: ${validValues.join(', ')}` 
                    };
                }
            }
        }
    }

    // Return normalized device and command in response
    return { valid: true, device: normalizedDevice, command: normalizedCommand };
}

/**
 * Format device command for serial transmission
 * @param {string} device - Device name
 * @param {string} command - Command name
 * @param {object} args - Command arguments
 * @returns {string} Formatted command (DEVICE:COMMAND[:ARGS])
 */
function formatDeviceCommand(device, command, args) {
    let cmd = `${device}:${command}`;
    
    if (args && typeof args === 'object' && Object.keys(args).length > 0) {
        // Map of commands that use positional arguments (just the value, not key=value)
        const positionalCommands = {
            'move': 'degrees',           // move:90
            'rotate': 'delta_degrees',   // rotate:45
            'spin': 'speed_us',          // spin:2000
            'speed': 'speed_us',         // speed:2000
            'set_range': 'centimeters',  // set_range:100
            'set_velocity': 'meters_per_second'  // set_velocity:5.0
        };

        const cmdKey = positionalCommands[command];
        
        if (cmdKey && args[cmdKey] !== undefined) {
            // Use positional argument format (just the value)
            const value = args[cmdKey];
            cmd += `:${value}`;
            logger.debug(`[FORMAT] Positional: ${command} uses key="${cmdKey}" with value="${value}" → ${cmd}`);
        } else {
            // Fall back to key=value format for unknown commands or multiple args
            const argPairs = Object.entries(args)
                .map(([key, val]) => `${key}=${val}`)
                .join(':');
            cmd += `:${argPairs}`;
            logger.debug(`[FORMAT] Key=value: ${command} formatted as ${cmd}`);
        }
    } else {
        logger.debug(`[FORMAT] No args: ${command} formatted as ${cmd}`);
    }

    logger.info(`[COMMAND] Final format: ${cmd}`);
    return cmd;
}

/**
 * Get all available commands for reference
 * @returns {object} Device commands structure
 */
function getAvailableCommands() {
    return deviceCommands;
}

/**
 * Get info about a specific device
 * @param {string} device - Device name (case-insensitive)
 * @returns {object} Device command info
 */
function getDeviceInfo(device) {
    const normalizedDevice = device.toUpperCase();
    
    if (!deviceCommands[normalizedDevice]) {
        return { error: `Unknown device: ${device}` };
    }

    return {
        device: normalizedDevice,
        commands: deviceCommands[normalizedDevice]
    };
}

module.exports = {
    validateDeviceCommand,
    formatDeviceCommand,
    getAvailableCommands,
    getDeviceInfo,
    deviceCommands
};
