const logger = require('../utils/logger');
const deviceCommands = require('../config/deviceCommands.json');

/**
 * Validate if a device command is valid
 * @param {string} device - Device name (STEPPER, RADAR, ACTUATOR)
 * @param {string} command - Command name (STATUS, START, etc)
 * @param {any} args - Command arguments
 * @returns {object} { valid: boolean, error?: string }
 */
function validateDeviceCommand(device, command, args) {
    // Check if device exists
    if (!deviceCommands[device]) {
        return { valid: false, error: `Unknown device: ${device}` };
    }

    // Check if command exists for device
    if (!deviceCommands[device][command]) {
        const available = Object.keys(deviceCommands[device]).join(', ');
        return { valid: false, error: `Unknown command for ${device}: ${command}. Available: ${available}` };
    }

    const cmdDef = deviceCommands[device][command];
    
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

    return { valid: true };
}

/**
 * Format device command for serial transmission
 * @param {string} device - Device name
 * @param {string} command - Command name
 * @param {object} args - Command arguments
 * @returns {string} Formatted command (DEVICE:COMMAND[:KEY=VALUE:...])
 */
function formatDeviceCommand(device, command, args) {
    let cmd = `${device}:${command}`;
    
    if (args && typeof args === 'object' && Object.keys(args).length > 0) {
        const argPairs = Object.entries(args)
            .map(([key, val]) => `${key}=${val}`)
            .join(':');
        cmd += `:${argPairs}`;
    }

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
 * @param {string} device - Device name
 * @returns {object} Device command info
 */
function getDeviceInfo(device) {
    if (!deviceCommands[device]) {
        return { error: `Unknown device: ${device}` };
    }

    return {
        device,
        commands: deviceCommands[device]
    };
}

module.exports = {
    validateDeviceCommand,
    formatDeviceCommand,
    getAvailableCommands,
    getDeviceInfo,
    deviceCommands
};
