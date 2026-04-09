const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const os = require('os');
require('dotenv').config();

const logger = require('./utils/logger');

// Create Pico controller for all UART device communication
class PicoController {
    async initialize() { logger.info('Pico controller (stub)'); }
    isInitialized() { return false; }
    isConnected() { return false; }
    getStatus() { return {}; }
    async sendCommand() { throw new Error('Pico not available'); }
    async stop() {}
}

// Routes
const apiRoutes = require('./routes/api');

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
        
        // Initialize PicoController for all UART device communication
        this.picoController = new PicoController(this.io);

        
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
        // Security middleware with CSP for self-hosted resources only
        this.app.use(helmet({
            contentSecurityPolicy: {
                directives: {
                    defaultSrc: ["'self'"],
                    scriptSrc: ["'self'", "'unsafe-inline'"],
                    styleSrc: ["'self'", "'unsafe-inline'"],
                    connectSrc: ["'self'"],
                    fontSrc: ["'self'"],
                    imgSrc: ["'self'", "data:"],
                    mediaSrc: ["'self'"],
                    objectSrc: ["'none'"]
                }
            },
            crossOriginOpenerPolicy: false,
            originAgentCluster: false,
            hsts: false  // Disable HSTS to allow HTTP
        }));
        
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
        
        // Protocol consistency middleware - ensure no unwanted redirects
        this.app.use((req, res, next) => {
            // Don't auto-redirect to HTTPS
            res.setHeader('X-Forwarded-Proto', 'http');
            next();
        });
        
        // Serve static files from client build (both production and development)
        const clientDistPath = path.join(__dirname, '../client/dist');
        this.app.use(express.static(clientDistPath, {
            maxAge: process.env.NODE_ENV === 'production' ? '1d' : 0
        }));
        logger.info(`Serving static files from: ${clientDistPath}`);
    }
    
    setupRoutes() {
        // API routes
        this.app.use('/api', apiRoutes);
        
        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'ok',
                timestamp: new Date().toISOString(),
                uptime: process.uptime(),
                // version: require('../package.json').version,
                pico: this.picoController?.isInitialized?.() || false
            });
        });
        
        // Serve client app for all other routes (SPA fallback)
        this.app.get('*', (req, res) => {
            const indexPath = path.join(__dirname, '../client/dist/index.html');
            res.sendFile(indexPath, (err) => {
                if (err) {
                    logger.error(`Failed to serve index.html: ${err.message}`);
                    res.status(404).json({ error: 'Client not found. Please run: npm run build', path: indexPath });
                }
            });
        });
        
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
                pico: this.picoController?.getStatus?.() || { status: 'unavailable', initialized: false }
            });
            
            // Stepper motor control - routes through Pico Master UART
            socket.on('stepper:start', (data) => {
                logger.info(`Stepper start requested by ${socket.id}:`, data);
                try {
                    this.picoController.sendCommand('STEPPER_START', data);
                } catch (error) {
                    socket.emit('stepper:error', { error: error.message });
                }
            });
            
            socket.on('stepper:stop', () => {
                logger.info(`Stepper stop requested by ${socket.id}`);
                try {
                    this.picoController.sendCommand('STEPPER_STOP');
                } catch (error) {
                    socket.emit('stepper:error', { error: error.message });
                }
            });
            
            socket.on('stepper:setSpeed', (speed) => {
                logger.info(`Stepper speed change requested by ${socket.id}: ${speed}`);
                try {
                    this.picoController.sendCommand('STEPPER_SET_SPEED', { speed });
                } catch (error) {
                    socket.emit('stepper:error', { error: error.message });
                }
            });
            
            socket.on('stepper:setDirection', (direction) => {
                logger.info(`Stepper direction change requested by ${socket.id}: ${direction}`);
                try {
                    this.picoController.sendCommand('STEPPER_SET_DIRECTION', { direction });
                } catch (error) {
                    socket.emit('stepper:error', { error: error.message });
                }
            });
            
            // Radar control - routes through Pico Master UART
            socket.on('radar:start', () => {
                logger.info(`Radar start requested by ${socket.id}`);
                try {
                    this.picoController.sendCommand('RADAR_START');
                } catch (error) {
                    socket.emit('radar:error', { error: error.message });
                }
            });
            
            socket.on('radar:stop', () => {
                logger.info(`Radar stop requested by ${socket.id}`);
                try {
                    this.picoController.sendCommand('RADAR_STOP');
                } catch (error) {
                    socket.emit('radar:error', { error: error.message });
                }
            });
            
            socket.on('radar:configure', (config) => {
                logger.info(`Radar config requested by ${socket.id}:`, config);
                try {
                    this.picoController.sendCommand('RADAR_CONFIG', config);
                } catch (error) {
                    socket.emit('radar:error', { error: error.message });
                }
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
            // Initialize Pico controller (all device communication through Master UART)
            try {
                await this.picoController.initialize();
                logger.info('Pico controller initialized');
            } catch (error) {
                logger.warn('Failed to initialize Pico controller:', error.message);
                logger.warn('Continuing with Pico controller unavailable');
            }
            
            
            // Start the server on all network interfaces (0.0.0.0) to allow connections from other computers
            this.server.listen(this.port, '0.0.0.0', () => {
                logger.info(`Radar Full Stack Server running on port ${this.port}`);
                logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
                logger.info(`Hostname: ${this.hostname}`);
                
                // Log accessible URLs
                logger.info('\n========== ACCESS POINTS ==========');
                logger.info(`Local:    http://localhost:${this.port}`);
                logger.info(`Hostname: http://${this.hostname}:${this.port}`);
                logger.info(`mDNS:     http://${this.hostname}.local:${this.port}`);
                logger.info('\nCORS Origins Allowed:');
                this.corsOrigins.forEach(origin => {
                    logger.info(`  - ${origin}`);
                });
                logger.info('===================================\n');
                
                // Start status broadcasting
                this.startStatusBroadcast();
                
                // Start background Pico reconnection attempts
                this.startPicoReconnection();
            });
            
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
                pico: this.picoController?.getStatus?.() || { status: 'unavailable' },
                system: {
                    uptime: process.uptime(),
                    memory: process.memoryUsage(),
                    cpu: process.cpuUsage()
                }
            };
            
            this.io.emit('system:status', status);
        }, 5000);
    }
    
    startPicoReconnection() {
        // Attempt to reconnect to Pico every 10 seconds
        this.picoReconnectInterval = setInterval(async () => {
            try {
                logger.debug('Attempting to reconnect to Pico Master...');
                if (this.picoController?.initialize) {
                    await this.picoController.initialize();
                    logger.info('Pico controller reconnection/reinitialization attempted');
                }
            } catch (error) {
                logger.debug('Pico reconnection attempt failed, will retry...', error.message);
            }
        }, 10000);
    }
    
    async restartSystem() {
        logger.info('Restarting system...');
        
        try {
            // Stop Pico controller
            if (this.picoController?.stop) await this.picoController.stop();
            
            // Clear intervals
            if (this.statusInterval) {
                clearInterval(this.statusInterval);
            }
            
            // Reinitialize Pico controller
            if (this.picoController?.initialize) {
                try {
                    await this.picoController.initialize();
                } catch (error) {
                    logger.warn('Failed to reinitialize Pico:', error.message);
                }
            }
            
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
            // Stop Pico controller
            if (this.picoController?.isInitialized?.()) {
                try {
                    await this.picoController.stop();
                } catch (error) {
                    logger.warn('Error stopping Pico controller:', error.message);
                }
            }
            
            // Clear intervals
            if (this.statusInterval) {
                clearInterval(this.statusInterval);
            }
            
            if (this.picoReconnectInterval) {
                clearInterval(this.picoReconnectInterval);
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