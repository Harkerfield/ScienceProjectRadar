const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const os = require('os');
require('dotenv').config();

const logger = require('./utils/logger');
const StepperController = require('./controllers/stepperController');
const RadarController = require('./controllers/radarController');
const PicoController = require('./controllers/picoController');
const BluetoothController = require('./controllers/bluetoothController');
const WiFiController = require('./controllers/wifiController');

// Pico-based controllers and serial communication
const { getInstance: getSerialInstance } = require('./utils/picoMasterSerial');
const PicoStepperController = require('./controllers/picoStepperController');
const PicoActuatorController = require('./controllers/picoActuatorController');

// Routes
const apiRoutes = require('./routes/api');
const stepperRoutes = require('./routes/stepper');
const radarRoutes = require('./routes/radar');
const actuatorRoutes = require('./routes/actuatorApi');

class RadarFullStackServer {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        
        // Get hostname for CORS and Socket.io configuration
        this.hostname = os.hostname();
        this.corsOrigins = this.getCorsOrigins();
        
        this.io = socketIo(this.server, {
            cors: {
                origin: this.corsOrigins,
                methods: ["GET", "POST"],
                credentials: true
            }
        });
        
        this.port = process.env.PORT || 3000;
        
        // Initialize Pico serial communication (singleton)
        this.serialComm = getSerialInstance();
        
        // Initialize controllers - using Pico-based controllers for device communication
        this.stepperController = new PicoStepperController(this.serialComm);
        this.actuatorController = new PicoActuatorController(this.serialComm);
        this.radarController = new RadarController(this.io);
        this.picoController = new PicoController(this.io);
        this.bluetoothController = new BluetoothController(this.io);
        this.wifiController = new WiFiController(this.io);
        
        this.setupMiddleware();
        this.setupRoutes();
        this.setupSocketEvents();
        
        logger.info('Radar Full Stack Server initialized');
    }
    
    getCorsOrigins() {
        const origins = [
            'http://localhost:3000',
            'http://localhost:8080',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:8080',
            process.env.CLIENT_URL || ''
        ];
        
        // Add hostname-based URLs
        if (this.hostname) {
            origins.push(`http://${this.hostname}:3000`);
            origins.push(`http://${this.hostname}:8080`);
            origins.push(`http://${this.hostname}.local:3000`);
            origins.push(`http://${this.hostname}.local:8080`);
        }
        
        // Filter out empty strings
        return origins.filter(o => o && o.length > 0);
    }
    
    setupMiddleware() {
        // Security middleware
        this.app.use(helmet());
        
        // CORS configuration - allow all configured origins
        this.app.use(cors({
            origin: (origin, callback) => {
                // Allow requests with no origin (like mobile apps or curl requests)
                if (!origin) return callback(null, true);
                
                // Check if origin is in allowed list
                if (this.corsOrigins.includes(origin)) {
                    callback(null, true);
                } else {
                    // Also allow if hostname matches
                    const requestHostname = origin.split('//')[1]?.split(':')[0];
                    if (requestHostname && requestHostname.includes(this.hostname)) {
                        callback(null, true);
                    } else {
                        logger.warn(`Rejected CORS request from origin: ${origin}`);
                        callback(null, false);
                    }
                }
            },
            credentials: true
        }));
        
        // Body parsing middleware
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));
        
        // Logging middleware
        this.app.use((req, res, next) => {
            logger.info(`${req.method} ${req.url} - ${req.ip}`);
            next();
        });
        
        // Serve static files from client build
        if (process.env.NODE_ENV === 'production') {
            this.app.use(express.static(path.join(__dirname, '../client/dist')));
        }
    }
    
    setupRoutes() {
        // API routes
        this.app.use('/api', apiRoutes);
        this.app.use('/api/stepper', stepperRoutes(this.stepperController));
        this.app.use('/api/actuator', actuatorRoutes(this.actuatorController));
        this.app.use('/api/radar', radarRoutes(this.radarController));
        
        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'ok',
                timestamp: new Date().toISOString(),
                uptime: process.uptime(),
                version: require('../package.json').version,
                controllers: {
                    stepper: this.stepperController.isInitialized(),
                    radar: this.radarController.isInitialized(),
                    pico: this.picoController.isInitialized(),
                    bluetooth: this.bluetoothController.isInitialized(),
                    wifi: this.wifiController.isConnected()
                }
            });
        });
        
        // Serve client app for all other routes (SPA)
        if (process.env.NODE_ENV === 'production') {
            this.app.get('*', (req, res) => {
                res.sendFile(path.join(__dirname, '../client/dist/index.html'));
            });
        }
        
        // Error handling middleware
        this.app.use((err, req, res, next) => {
            logger.error(`Error handling request: ${err.message}`, err);
            res.status(500).json({
                error: 'Internal server error',
                message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
            });
        });
    }
    
    setupSocketEvents() {
        this.io.on('connection', (socket) => {
            logger.info(`Client connected: ${socket.id}`);
            
            // Send initial system status
            socket.emit('system:status', {
                controllers: {
                    stepper: this.stepperController.getStatus(),
                    radar: this.radarController.getStatus(),
                    pico: this.picoController.getStatus(),
                    bluetooth: this.bluetoothController.getStatus(),
                    wifi: this.wifiController.getStatus()
                }
            });
            
            // Stepper motor control events
            socket.on('stepper:start', (data) => {
                logger.info(`Stepper start requested by ${socket.id}:`, data);
                this.stepperController.startRotation(data);
            });
            
            socket.on('stepper:stop', () => {
                logger.info(`Stepper stop requested by ${socket.id}`);
                this.stepperController.stopRotation();
            });
            
            socket.on('stepper:setSpeed', (speed) => {
                logger.info(`Stepper speed change requested by ${socket.id}: ${speed}`);
                this.stepperController.setRotationSpeed(speed);
            });
            
            socket.on('stepper:setDirection', (direction) => {
                logger.info(`Stepper direction change requested by ${socket.id}: ${direction}`);
                this.stepperController.setDirection(direction);
            });
            
            // Radar control events
            socket.on('radar:start', () => {
                logger.info(`Radar start requested by ${socket.id}`);
                this.radarController.startScanning();
            });
            
            socket.on('radar:stop', () => {
                logger.info(`Radar stop requested by ${socket.id}`);
                this.radarController.stopScanning();
            });
            
            socket.on('radar:configure', (config) => {
                logger.info(`Radar config requested by ${socket.id}:`, config);
                this.radarController.updateConfiguration(config);
            });
            
            // Pico control events
            socket.on('pico:sendCommand', (data) => {
                logger.info(`Pico command requested by ${socket.id}:`, data);
                try {
                    this.picoController.sendCommand(data.command, data.params);
                } catch (error) {
                    socket.emit('pico:commandError', { error: error.message });
                }
            });
            
            socket.on('pico:requestStatus', () => {
                logger.info(`Pico status requested by ${socket.id}`);
                try {
                    this.picoController.requestStatus();
                } catch (error) {
                    socket.emit('pico:commandError', { error: error.message });
                }
            });
            
            socket.on('pico:controlServo', (action) => {
                logger.info(`Pico servo control requested by ${socket.id}: ${action}`);
                try {
                    this.picoController.controlServo(action);
                } catch (error) {
                    socket.emit('pico:commandError', { error: error.message });
                }
            });
            
            // System control events
            socket.on('system:restart', () => {
                logger.info(`System restart requested by ${socket.id}`);
                this.restartSystem();
            });
            
            socket.on('system:shutdown', () => {
                logger.info(`System shutdown requested by ${socket.id}`);
                this.shutdownSystem();
            });
            
            // Connection management
            socket.on('disconnect', () => {
                logger.info(`Client disconnected: ${socket.id}`);
            });
            
            socket.on('error', (error) => {
                logger.error(`Socket error from ${socket.id}:`, error);
            });
        });
    }
    
    async start() {
        try {
            // Initialize serial communication for Pico devices
            logger.info('Initializing Pico serial communication...');
            try {
                await this.serialComm.connect();
                logger.info('Pico serial communication established');
            } catch (error) {
                logger.warn('Failed to connect to Pico:', error.message);
                logger.warn('Continuing without Pico support');
            }
            
            // Initialize Pico-based controllers
            await this.stepperController.initialize();
            await this.actuatorController.initialize();
            
            // Initialize other controllers
            await this.radarController.initialize();
            
            // Initialize Pico controller if enabled
            if (process.env.PICO_UART_ENABLED === 'true') {
                await this.picoController.initialize();
            }
            
            await this.bluetoothController.initialize();
            await this.wifiController.initialize();
            
            // Start the server
            this.server.listen(this.port, () => {\n                logger.info(`Radar Full Stack Server running on port ${this.port}`);\n                logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);\n                logger.info(`Hostname: ${this.hostname}`);\n                \n                // Log accessible URLs\n                logger.info('\\n========== ACCESS POINTS ==========');\n                logger.info(`Local:    http://localhost:${this.port}`);\n                logger.info(`Hostname: http://${this.hostname}:${this.port}`);\n                logger.info(`mDNS:     http://${this.hostname}.local:${this.port}`);\n                logger.info(`\\nCORS Origins Allowed:`);\n                this.corsOrigins.forEach(origin => {\n                    logger.info(`  - ${origin}`);\n                });\n                logger.info('===================================\\n');\n                \n                // Start status broadcasting\n                this.startStatusBroadcast();\n            });
            
        } catch (error) {
            logger.error('Failed to start server:', error);
            process.exit(1);
        }
    }
    
    startStatusBroadcast() {
        // Broadcast system status every 5 seconds
        this.statusInterval = setInterval(() => {
            const status = {
                timestamp: new Date().toISOString(),
                controllers: {
                    stepper: this.stepperController.getStatus(),
                    radar: this.radarController.getStatus(),
                    pico: this.picoController.getStatus(),
                    bluetooth: this.bluetoothController.getStatus(),
                    wifi: this.wifiController.getStatus()
                },
                system: {
                    uptime: process.uptime(),
                    memory: process.memoryUsage(),
                    cpu: process.cpuUsage()
                }
            };
            
            this.io.emit('system:status', status);
        }, 5000);
    }
    
    async restartSystem() {
        logger.info('Restarting system...');
        
        try {
            // Stop all controllers
            await this.stepperController.stop();
            await this.radarController.stop();
            await this.bluetoothController.stop();
            
            // Clear intervals
            if (this.statusInterval) {
                clearInterval(this.statusInterval);
            }
            
            // Restart controllers
            await this.stepperController.initialize();
            await this.radarController.initialize();
            
            if (process.env.PICO_UART_ENABLED === 'true') {
                await this.picoController.initialize();
            }
            
            await this.bluetoothController.initialize();
            
            this.io.emit('system:restarted');
            logger.info('System restarted successfully');
            
        } catch (error) {
            logger.error('Error restarting system:', error);
            this.io.emit('system:error', { message: 'Failed to restart system' });
        }
    }
    
    async shutdownSystem() {
        logger.info('Shutting down system...');
        
        try {
            // Stop all controllers
            await this.stepperController.stop();
            await this.radarController.stop();
            
            if (this.picoController.isInitialized()) {
                await this.picoController.stop();
            }
            
            await this.bluetoothController.stop();
            
            // Clear intervals
            if (this.statusInterval) {
                clearInterval(this.statusInterval);
            }
            
            // Close server
            this.server.close(() => {
                logger.info('Server shut down successfully');
                process.exit(0);
            });
            
        } catch (error) {
            logger.error('Error shutting down system:', error);
            process.exit(1);
        }
    }
}

// Handle process events
process.on('SIGINT', () => {
    logger.info('Received SIGINT, shutting down gracefully...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    logger.info('Received SIGTERM, shutting down gracefully...');
    process.exit(0);
});

process.on('uncaughtException', (error) => {
    logger.error('Uncaught exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

// Create and start server
const server = new RadarFullStackServer();
server.start();

module.exports = RadarFullStackServer;