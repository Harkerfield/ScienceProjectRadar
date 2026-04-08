const logger = require('../utils/logger');

class StepperController {
    constructor(io, uartController) {
        this.io = io;
        this.uartController = uartController;
        this.isRunning = false;
        this.currentSpeed = 100; // RPM
        this.currentDirection = 1; // 1 for clockwise, -1 for counterclockwise
        this.totalSteps = 0;
        this.initialized = false;
        
        // Stepper motor configuration
        this.config = {
            stepsPerRevolution: 200,
            maxSpeed: 500,
            minSpeed: 10,
            acceleration: 50
        };
        
        logger.info('Stepper controller created (UART-based)');
    }
    
    async initialize() {
        try {
            logger.info('Initializing stepper motor controller (via UART)...');
            this.initialized = true;
            
            this.io.emit('stepper:initialized', {
                config: this.config,
                status: this.getStatus()
            });
            
            logger.info('Stepper motor controller initialized successfully');
            return true;
        } catch (error) {
            logger.error('Error initializing stepper controller:', error);
            throw error;
        }
    }
    
    startRotation(options = {}) {
        if (!this.initialized) {
            const error = 'Stepper motor not initialized';
            logger.error(error);
            this.io.emit('stepper:error', { message: error });
            return false;
        }
        
        try {
            const speed = options.speed || this.currentSpeed;
            const direction = options.direction || this.currentDirection;
            
            this.setRotationSpeed(speed);
            this.setDirection(direction);
            this.isRunning = true;
            
            logger.info(`Started stepper motor: speed=${speed} RPM, direction=${direction > 0 ? 'CW' : 'CCW'}`);
            
            this.io.emit('stepper:started', {
                speed: this.currentSpeed,
                direction: this.currentDirection,
                timestamp: new Date().toISOString()
            });
            
            return true;
        } catch (error) {
            logger.error('Error starting stepper motor:', error);
            this.io.emit('stepper:error', { message: error.message });
            return false;
        }
    }
    
    stopRotation() {
        if (!this.initialized) {
            logger.warn('Stepper motor not initialized');
            return false;
        }
        
        try {
            this.isRunning = false;
            logger.info('Stopped stepper motor');
            
            this.io.emit('stepper:stopped', {
                totalSteps: this.totalSteps,
                timestamp: new Date().toISOString()
            });
            
            return true;
        } catch (error) {
            logger.error('Error stopping stepper motor:', error);
            this.io.emit('stepper:error', { message: error.message });
            return false;
        }
    }
    
    setRotationSpeed(speed) {
        if (!this.initialized) {
            logger.warn('Stepper motor not initialized');
            return false;
        }
        
        try {
            const clampedSpeed = Math.max(this.config.minSpeed, Math.min(this.config.maxSpeed, speed));
            this.currentSpeed = clampedSpeed;
            
            logger.info(`Set stepper motor speed to ${clampedSpeed} RPM`);
            
            this.io.emit('stepper:speedChanged', {
                speed: clampedSpeed,
                timestamp: new Date().toISOString()
            });
            
            return true;
        } catch (error) {
            logger.error('Error setting stepper motor speed:', error);
            this.io.emit('stepper:error', { message: error.message });
            return false;
        }
    }
    
    setDirection(direction) {
        if (!this.initialized) {
            logger.warn('Stepper motor not initialized');
            return false;
        }
        
        try {
            const normalizedDirection = direction > 0 ? 1 : -1;
            this.currentDirection = normalizedDirection;
            
            const directionName = normalizedDirection > 0 ? 'Clockwise' : 'Counter-clockwise';
            logger.info(`Set stepper motor direction to ${directionName}`);
            
            this.io.emit('stepper:directionChanged', {
                direction: normalizedDirection,
                directionName: directionName,
                timestamp: new Date().toISOString()
            });
            
            return true;
        } catch (error) {
            logger.error('Error setting stepper motor direction:', error);
            this.io.emit('stepper:error', { message: error.message });
            return false;
        }
    }
    
    getStatus() {
        return {
            initialized: this.initialized,
            isRunning: this.isRunning,
            currentSpeed: this.currentSpeed,
            currentDirection: this.currentDirection,
            totalSteps: this.totalSteps,
            totalRevolutions: this.totalSteps / this.config.stepsPerRevolution,
            config: this.config,
            controlledBy: 'UART Master API'
        };
    }
    
    isInitialized() {
        return this.initialized;
    }
    
    async stop() {
        logger.info('Stopping stepper controller...');
        this.stopRotation();
        this.initialized = false;
        logger.info('Stepper controller stopped');
    }
    
    updateStatus(status) {
        if (status.totalSteps !== undefined) {
            this.totalSteps = status.totalSteps;
        }
        if (status.isRunning !== undefined) {
            this.isRunning = status.isRunning;
        }
        if (status.currentSpeed !== undefined) {
            this.currentSpeed = status.currentSpeed;
        }
        if (status.currentDirection !== undefined) {
            this.currentDirection = status.currentDirection;
        }
    }
}

module.exports = StepperController;