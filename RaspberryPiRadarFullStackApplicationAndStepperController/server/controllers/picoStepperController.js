const logger = require('../utils/logger');

/**
 * PicoStepperController
 * Handles communication with Stepper Pico slave via Master Pico
 * Sends commands via UART using format: STEPPER:COMMAND[:ARGS]
 * Receives responses in format: STEPPER:OK[:KEY=VALUE:...]
 */
class PicoStepperController {
    constructor(serialComm) {
        this.serialComm = serialComm;
        this.device = 'STEPPER';
        this.initialized = false;
        
        // Cache state to reduce device queries
        this.cache = {
            position: 0,
            calibrated: false,
            rotating: false,
            direction: 'CW',
            enabled: false,
            speed: 2000,
            sensorState: 0,
            lastUpdate: null
        };
        
        // Configuration
        this.config = {
            MIN_SPEED_US: 500,
            MAX_SPEED_US: 10000,
            DEFAULT_SPEED: 2000,
            TIMEOUT_MS: 5000
        };
    }
    
    /**
     * Initialize the controller and connect to device
     */
    async initialize() {
        try {
            // Connect to Pico if not already connected
            if (!this.serialComm.isConnected) {
                await this.serialComm.connect();
                logger.info('Serial communication initialized');
            }
            
            // Test connection with PING
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'PING',
                null,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                logger.info('Stepper controller connected and ready');
                this.initialized = true;
                return true;
            } else {
                logger.warn('Stepper device not responding to PING');
                this.initialized = false;
                return false;
            }
        } catch (error) {
            logger.error('Failed to initialize stepper controller:', error);
            this.initialized = false;
            return false;
        }
    }
    
    /**
     * Check if initialized
     */
    isInitialized() {
        return this.initialized;
    }
    
    /**
     * Stop/cleanup
     */
    async stop() {
        try {
            // Optional: disable motor on stop
            await this.serialComm.sendDeviceCommand(
                this.device,
                'DISABLE',
                null,
                this.config.TIMEOUT_MS
            );
            this.initialized = false;
        } catch (error) {
            logger.warn('Error disabling stepper on stop:', error);
        }
    }
    
    /**
     * Get status for health checks
     */
    getStatus() {
        return {
            initialized: this.initialized,
            device: this.device,
            cached: this.cache
        };
    }
    
    /**
     * ===== GET ENDPOINTS (Read-Only) =====
     */
    
    /**
     * Get heartbeat/alive status
     */
    async getHeartbeat() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device, 
                'PING', 
                null, 
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                return {
                    success: true,
                    data: {
                        alive: true,
                        message: response.data.msg || 'Device responding',
                        timestamp: response.timestamp
                    }
                };
            }
            return this._errorResponse('Device not responding', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error getting heartbeat:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get current speed setting
     */
    async getSpeed() {
        try {
            // Return cached or query device
            return {
                success: true,
                data: {
                    speed: this.cache.speed,
                    min: this.config.MIN_SPEED_US,
                    max: this.config.MAX_SPEED_US,
                    unit: 'microseconds'
                }
            };
        } catch (error) {
            logger.error('Error getting speed:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get enable/disable status
     */
    async getEnabled() {
        try {
            return {
                success: true,
                data: { 
                    enabled: this.cache.enabled 
                }
            };
        } catch (error) {
            logger.error('Error getting enabled status:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get current direction
     */
    async getDirection() {
        try {
            return {
                success: true,
                data: { 
                    direction: this.cache.direction 
                }
            };
        } catch (error) {
            logger.error('Error getting direction:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get current position in degrees
     */
    async getPosition() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'STATUS',
                null,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                const pos = response.data.position || 0;
                this.cache.position = pos;
                this.cache.calibrated = response.data.calibrated === 1 || response.data.calib === 1;
                
                return {
                    success: true,
                    data: {
                        position: pos,
                        degrees: pos,
                        calibrated: this.cache.calibrated
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to get position', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error getting position:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get home position status
     */
    async getAtHome() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'STATUS',
                null,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                const position = response.data.position || 0;
                const atHome = Math.abs(position) < 1; // Within 1 degree of home
                
                return {
                    success: true,
                    data: {
                        atHome: atHome,
                        position: position
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to check home status', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error getting home status:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get current speed in microseconds
     */
    async getCurrentSpeed() {
        try {
            return {
                success: true,
                data: {
                    currentSpeed: this.cache.speed,
                    microSeconds: this.cache.speed
                }
            };
        } catch (error) {
            logger.error('Error getting current speed:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get home calibration status
     */
    async getHomeCalibrated() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'STATUS',
                null,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                const calibrated = response.data.calibrated === 1 || response.data.calib === 1;
                this.cache.calibrated = calibrated;
                
                return {
                    success: true,
                    data: {
                        calibrated: calibrated,
                        homeFound: calibrated
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to get calibration status', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error getting calibration status:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get continuous rotation status
     */
    async getContinuousRotating() {
        try {
            return {
                success: true,
                data: {
                    rotating: this.cache.rotating,
                    direction: this.cache.rotating ? this.cache.direction : null
                }
            };
        } catch (error) {
            logger.error('Error getting rotation status:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get maximum speed limit
     */
    async getMaxSpeed() {
        try {
            return {
                success: true,
                data: { 
                    maxSpeed: this.config.MAX_SPEED_US,
                    microSeconds: this.config.MAX_SPEED_US
                }
            };
        } catch (error) {
            logger.error('Error getting max speed:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get minimum speed limit
     */
    async getMinSpeed() {
        try {
            return {
                success: true,
                data: { 
                    minSpeed: this.config.MIN_SPEED_US,
                    microSeconds: this.config.MIN_SPEED_US
                }
            };
        } catch (error) {
            logger.error('Error getting min speed:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get home sensor state
     */
    async getSensorState() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'SENSOR',
                null,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                const sensor = response.data.sensor || 0;
                this.cache.sensorState = sensor;
                
                return {
                    success: true,
                    data: {
                        sensor: sensor,
                        triggered: sensor === 1,
                        state: sensor === 1 ? 'triggered' : 'clear'
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to get sensor state', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error getting sensor state:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Get complete system status
     */
    async getStatus() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'STATUS',
                null,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                // Update cache
                this.cache.position = response.data.position || 0;
                this.cache.calibrated = response.data.calibrated === 1 || response.data.calib === 1;
                this.cache.enabled = response.data.enabled === 1 || response.data.ena === 1;
                
                return {
                    success: true,
                    data: {
                        position: this.cache.position,
                        enabled: this.cache.enabled,
                        calibrated: this.cache.calibrated,
                        direction: this.cache.direction,
                        speed: this.cache.speed,
                        rotating: this.cache.rotating,
                        atHome: Math.abs(this.cache.position) < 1,
                        sensor: this.cache.sensorState,
                        state: response.data.state || 'unknown'
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to get status', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error getting status:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * ===== PUT ENDPOINTS (State Modification) =====
     */
    
    /**
     * Calibrate home position (2-phase homing)
     */
    async findHome() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'HOME',
                null,
                8000 // Longer timeout for homing
            );
            
            if (response.success) {
                this.cache.position = 0;
                this.cache.calibrated = true;
                
                return {
                    success: true,
                    data: {
                        message: 'Home calibrated successfully',
                        position: 0,
                        calibrated: true
                    }
                };
            }
            return this._errorResponse(response.error || 'Home calibration failed', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error finding home:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Move to absolute angle position
     */
    async moveToAngle(angle) {
        try {
            if (typeof angle !== 'number' || angle < 0 || angle > 360) {
                return this._errorResponse('Angle must be between 0-360 degrees', 'INVALID_PARAM');
            }
            
            if (!this.cache.calibrated) {
                return this._errorResponse('Must calibrate home first', 'NOT_CALIBRATED');
            }
            
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'MOVE',
                angle,
                5000
            );
            
            if (response.success) {
                this.cache.position = response.data.position || angle;
                
                return {
                    success: true,
                    data: {
                        message: `Moved to ${angle}°`,
                        position: this.cache.position,
                        target: angle
                    }
                };
            }
            return this._errorResponse(response.error || 'Move failed', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error moving to angle:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Rotate by relative degrees
     */
    async rotateByDegrees(degrees) {
        try {
            if (typeof degrees !== 'number') {
                return this._errorResponse('Degrees must be a number', 'INVALID_PARAM');
            }
            
            if (!this.cache.calibrated) {
                return this._errorResponse('Must calibrate home first', 'NOT_CALIBRATED');
            }
            
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'ROTATE',
                degrees,
                5000
            );
            
            if (response.success) {
                this.cache.position = response.data.position || (this.cache.position + degrees);
                
                return {
                    success: true,
                    data: {
                        message: `Rotated by ${degrees}°`,
                        position: this.cache.position,
                        delta: degrees
                    }
                };
            }
            return this._errorResponse(response.error || 'Rotation failed', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error rotating by degrees:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Set motor speed
     */
    async setSpeed(speedUs) {
        try {
            if (typeof speedUs !== 'number') {
                return this._errorResponse('Speed must be a number', 'INVALID_PARAM');
            }
            
            if (speedUs < this.config.MIN_SPEED_US || speedUs > this.config.MAX_SPEED_US) {
                return this._errorResponse(
                    `Speed must be between ${this.config.MIN_SPEED_US}-${this.config.MAX_SPEED_US} µs`,
                    'OUT_OF_RANGE'
                );
            }
            
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'SPEED',
                speedUs,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                this.cache.speed = speedUs;
                
                return {
                    success: true,
                    data: {
                        message: `Speed set to ${speedUs}µs`,
                        speed: speedUs,
                        unit: 'microseconds'
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to set speed', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error setting speed:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Enable motor
     */
    async setEnabled(enabled) {
        try {
            const cmd = enabled ? 'ENABLE' : 'DISABLE';
            
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                cmd,
                null,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                this.cache.enabled = enabled;
                
                return {
                    success: true,
                    data: {
                        message: enabled ? 'Motor enabled' : 'Motor disabled',
                        enabled: enabled
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to change enabled state', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error setting enabled state:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Start continuous rotation at default speed
     */
    async startContinuousRotation(direction) {
        try {
            if (!['CW', 'CCW'].includes(direction)) {
                return this._errorResponse('Direction must be "CW" or "CCW"', 'INVALID_PARAM');
            }
            
            // Start spinning at current speed
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'SPIN',
                this.cache.speed,
                this.config.TIMEOUT_MS
            );
            
            if (response.success) {
                this.cache.rotating = true;
                this.cache.direction = direction;
                
                return {
                    success: true,
                    data: {
                        message: `Started continuous rotation ${direction}`,
                        rotating: true,
                        direction: direction,
                        speed: this.cache.speed
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to start rotation', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error starting continuous rotation:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Set maximum speed limit (server-side configuration only)
     */
    async setMaxSpeed(maxSpeedUs) {
        try {
            if (typeof maxSpeedUs !== 'number' || maxSpeedUs <= 0) {
                return this._errorResponse('Max speed must be a positive number', 'INVALID_PARAM');
            }
            
            if (maxSpeedUs < this.config.MIN_SPEED_US) {
                return this._errorResponse('Max speed cannot be less than min speed', 'INVALID_PARAM');
            }
            
            this.config.MAX_SPEED_US = maxSpeedUs;
            
            return {
                success: true,
                data: {
                    message: `Max speed set to ${maxSpeedUs}µs`,
                    maxSpeed: maxSpeedUs
                }
            };
        } catch (error) {
            logger.error('Error setting max speed:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Set minimum speed limit (server-side configuration only)
     */
    async setMinSpeed(minSpeedUs) {
        try {
            if (typeof minSpeedUs !== 'number' || minSpeedUs <= 0) {
                return this._errorResponse('Min speed must be a positive number', 'INVALID_PARAM');
            }
            
            if (minSpeedUs > this.config.MAX_SPEED_US) {
                return this._errorResponse('Min speed cannot be greater than max speed', 'INVALID_PARAM');
            }
            
            this.config.MIN_SPEED_US = minSpeedUs;
            
            return {
                success: true,
                data: {
                    message: `Min speed set to ${minSpeedUs}µs`,
                    minSpeed: minSpeedUs
                }
            };
        } catch (error) {
            logger.error('Error setting min speed:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    
    /**
     * Create error response object
     */
    _errorResponse(message, code = 'ERROR') {
        return {
            success: false,
            error: message,
            code: code,
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = PicoStepperController;
