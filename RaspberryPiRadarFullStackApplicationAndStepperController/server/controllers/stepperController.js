const five = require('johnny-five');
const Raspi = require('raspi-io').RaspiIO;
const logger = require('../utils/logger');

class StepperController {
    constructor(io) {
        this.io = io;
        this.board = null;
        this.stepper = null;
        this.isRunning = false;
        this.currentSpeed = 100; // RPM
        this.currentDirection = 1; // 1 for clockwise, -1 for counterclockwise
        this.totalSteps = 0;
        this.initialized = false;
        
        // Stepper motor configuration
        this.config = {
            pins: [18, 19, 20, 21], // GPIO pins for stepper motor driver
            stepsPerRevolution: 200, // Standard for 1.8° step angle motors
            maxSpeed: 500, // Maximum RPM
            minSpeed: 10,  // Minimum RPM
            acceleration: 50, // Steps per second squared
            enablePin: 22 // Enable pin for motor driver
        };
        
        logger.info('Stepper controller created');
    }
    
    async initialize() {
        return new Promise((resolve, reject) => {
            try {
                logger.info('Initializing stepper motor controller...');
                
                // Initialize Johnny-Five board with Raspi-IO
                this.board = new five.Board({
                    io: new Raspi(),
                    repl: false,
                    debug: false
                });
                
                this.board.on('ready', () => {
                    try {
                        // Initialize stepper motor
                        this.stepper = new five.Stepper({
                            type: five.Stepper.TYPE.DRIVER,
                            stepsPerRev: this.config.stepsPerRevolution,
                            pins: {
                                step: this.config.pins[0],
                                dir: this.config.pins[1],
                                enable: this.config.enablePin
                            }
                        });
                        
                        // Set up motor parameters
                        this.stepper.rpm(this.currentSpeed);
                        this.stepper.direction(this.currentDirection);
                        
                        // Enable motor driver
                        this.enableMotor();
                        
                        this.initialized = true;
                        logger.info('Stepper motor controller initialized successfully');
                        
                        // Emit initialization event
                        this.io.emit('stepper:initialized', {
                            config: this.config,
                            status: this.getStatus()
                        });
                        
                        resolve();
                        
                    } catch (error) {
                        logger.error('Error setting up stepper motor:', error);
                        reject(error);
                    }
                });
                
                this.board.on('error', (error) => {
                    logger.error('Board error:', error);
                    reject(error);
                });
                
            } catch (error) {
                logger.error('Error initializing stepper controller:', error);
                reject(error);
            }
        });
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
            
            // Update speed and direction if provided
            this.setRotationSpeed(speed);
            this.setDirection(direction);
            
            // Enable motor and start continuous rotation
            this.enableMotor();
            this.isRunning = true;
            
            // Start continuous rotation
            this.startContinuousRotation();
            
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
            
            // Stop the motor
            if (this.stepper) {
                this.stepper.stop();
            }
            
            // Optionally disable motor to save power
            this.disableMotor();
            
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
            // Clamp speed to valid range
            const clampedSpeed = Math.max(this.config.minSpeed, Math.min(this.config.maxSpeed, speed));
            
            this.currentSpeed = clampedSpeed;
            
            if (this.stepper) {
                this.stepper.rpm(clampedSpeed);
            }
            
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
            // Normalize direction to 1 or -1
            const normalizedDirection = direction > 0 ? 1 : -1;
            this.currentDirection = normalizedDirection;
            
            if (this.stepper) {
                this.stepper.direction(normalizedDirection);
            }
            
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
    
    startContinuousRotation() {
        if (!this.isRunning || !this.stepper) return;
        
        // Use a large number of steps to simulate continuous rotation
        const stepsPerCycle = this.config.stepsPerRevolution * 10; // 10 revolutions at a time
        
        this.stepper.step(stepsPerCycle, () => {
            if (this.isRunning) {
                this.totalSteps += stepsPerCycle;
                
                // Emit progress update
                this.io.emit('stepper:progress', {
                    totalSteps: this.totalSteps,
                    revolutions: this.totalSteps / this.config.stepsPerRevolution,
                    timestamp: new Date().toISOString()
                });
                
                // Continue rotating
                this.startContinuousRotation();
            }
        });
    }
    
    enableMotor() {
        if (this.board) {
            // Set enable pin low to enable motor driver (assuming active low)
            this.board.digitalWrite(this.config.enablePin, 0);
            logger.info('Motor driver enabled');
        }
    }
    
    disableMotor() {
        if (this.board) {
            // Set enable pin high to disable motor driver (assuming active low)
            this.board.digitalWrite(this.config.enablePin, 1);
            logger.info('Motor driver disabled');
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
            config: this.config
        };
    }
    
    isInitialized() {
        return this.initialized;
    }
    
    async stop() {
        logger.info('Stopping stepper controller...');
        
        this.stopRotation();
        
        if (this.board) {
            try {
                await new Promise((resolve) => {
                    this.board.on('exit', resolve);
                    this.board.exit();
                });
            } catch (error) {
                logger.error('Error stopping board:', error);
            }
        }
        
        this.initialized = false;
        logger.info('Stepper controller stopped');
    }
    
    // Manual step control methods
    stepForward(steps = 1) {
        if (!this.initialized || this.isRunning) return false;
        
        this.stepper.step(steps, () => {
            this.totalSteps += steps;
            this.io.emit('stepper:stepped', {
                steps: steps,
                totalSteps: this.totalSteps,
                direction: 'forward'
            });
        });
        
        return true;
    }
    
    stepBackward(steps = 1) {
        if (!this.initialized || this.isRunning) return false;
        
        this.stepper.step(-steps, () => {
            this.totalSteps -= steps;
            this.io.emit('stepper:stepped', {
                steps: -steps,
                totalSteps: this.totalSteps,
                direction: 'backward'
            });
        });
        
        return true;
    }
    
    resetStepCount() {
        this.totalSteps = 0;
        this.io.emit('stepper:stepCountReset', {
            timestamp: new Date().toISOString()
        });
        
        logger.info('Step count reset to zero');
    }
}

module.exports = StepperController;