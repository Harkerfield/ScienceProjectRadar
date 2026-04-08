const logger = require('../utils/logger');

/**
 * PicoActuatorController
 * Handles communication with Actuator (Servo) Pico slave via Master Pico
 * Sends commands via UART using format: SERVO:COMMAND[:ARGS]
 * Receives responses in format: SERVO:OK[:KEY=VALUE:...]
 */
class PicoActuatorController {
    constructor(serialComm) {
        this.serialComm = serialComm;
        this.device = 'SERVO';
        this.initialized = false;
        
        // Cache state
        this.cache = {
            position: 0,
            state: 'unknown', // 'open', 'closed', 'unknown'
            isOpen: false
        };
        
        // Configuration
        this.config = {
            OPEN_POSITION: 100,
            CLOSED_POSITION: 0
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
                5000
            );
            
            if (response.success) {
                logger.info('Actuator controller connected and ready');
                this.initialized = true;
                return true;
            } else {
                logger.warn('Actuator device not responding to PING');
                this.initialized = false;
                return false;
            }
        } catch (error) {
            logger.error('Failed to initialize actuator controller:', error);
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
            // Optional: close actuator on stop
            await this.serialComm.sendDeviceCommand(
                this.device,
                'CLOSE',
                null,
                8000
            );
            this.initialized = false;
        } catch (error) {
            logger.warn('Error closing actuator on stop:', error);
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
                5000
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
     * Get actuator position (0-100%)
     */
    async getPosition() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'STATUS',
                null,
                5000
            );
            
            if (response.success) {
                const state = response.data.state || 'unknown';
                
                // Map state to position
                let position = 0;
                if (state === 'open') {
                    position = this.config.OPEN_POSITION;
                    this.cache.isOpen = true;
                } else if (state === 'closed') {
                    position = this.config.CLOSED_POSITION;
                    this.cache.isOpen = false;
                }
                
                this.cache.position = position;
                this.cache.state = state;
                
                return {
                    success: true,
                    data: {
                        position: position,
                        state: state,
                        percentage: position
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
     * Get complete actuator status
     */
    async getStatus() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'STATUS',
                null,
                5000
            );
            
            if (response.success) {
                const state = response.data.state || 'unknown';
                let position = 0;
                
                if (state === 'open') {
                    position = this.config.OPEN_POSITION;
                } else if (state === 'closed') {
                    position = this.config.CLOSED_POSITION;
                }
                
                this.cache.position = position;
                this.cache.state = state;
                
                return {
                    success: true,
                    data: {
                        position: position,
                        state: state,
                        isOpen: state === 'open',
                        isClosed: state === 'closed'
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
     * Open/extend the actuator
     */
    async open() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'OPEN',
                null,
                8000 // Longer timeout for mechanical movement
            );
            
            if (response.success) {
                this.cache.position = this.config.OPEN_POSITION;
                this.cache.state = 'open';
                this.cache.isOpen = true;
                
                return {
                    success: true,
                    data: {
                        message: 'Actuator opened',
                        state: 'open',
                        position: this.config.OPEN_POSITION,
                        isOpen: true
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to open actuator', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error opening actuator:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Close/retract the actuator
     */
    async close() {
        try {
            const response = await this.serialComm.sendDeviceCommand(
                this.device,
                'CLOSE',
                null,
                8000 // Longer timeout for mechanical movement
            );
            
            if (response.success) {
                this.cache.position = this.config.CLOSED_POSITION;
                this.cache.state = 'closed';
                this.cache.isOpen = false;
                
                return {
                    success: true,
                    data: {
                        message: 'Actuator closed',
                        state: 'closed',
                        position: this.config.CLOSED_POSITION,
                        isOpen: false
                    }
                };
            }
            return this._errorResponse(response.error || 'Failed to close actuator', 'DEVICE_ERROR');
        } catch (error) {
            logger.error('Error closing actuator:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Set actuator position (simplified to open/close)
     */
    async setPosition(position) {
        try {
            if (typeof position !== 'number' || position < 0 || position > 100) {
                return this._errorResponse('Position must be between 0-100', 'INVALID_PARAM');
            }
            
            // Map position percentage to open/close
            // 0-49% = close, 50-100% = open
            if (position < 50) {
                return await this.close();
            } else {
                return await this.open();
            }
        } catch (error) {
            logger.error('Error setting position:', error);
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * ===== HELPER METHODS =====
     */
    
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

module.exports = PicoActuatorController;
