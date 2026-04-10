const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const os = require('os');
require('dotenv').config();

const logger = require('./utils/logger');
const uartSerial = require('./utils/uartSerial');

// Create Pico controller for all UART device communication
class PicoController {
    constructor(io) {
        this.isInitialized = false;
        this.isConnected = false;
        this.io = io;
        this.lastStatus = null;
    }

    async initialize() {
        try {
            // Initialize UART connection
            await uartSerial.initialize();
            logger.info('[PICO] UART connection initialized');
            
            // Send MASTER:PING to verify Pico is online
            const response = await this.sendCommand('MASTER', 'PING');
            
            if (response && response.s === 'ok') {
                this.isConnected = true;
                this.isInitialized = true;
                logger.info('[PICO] Pico Master is online and responding');
                
                // Get full status
                this.lastStatus = await this.sendCommand('MASTER', 'STATUS');
                logger.info(`[PICO] Master status: ${JSON.stringify(this.lastStatus)}`);
                
                return { success: true, status: this.lastStatus };
            } else {
                throw new Error('Pico Master did not respond to PING');
            }
        } catch (err) {
            logger.error(`[PICO] Failed to initialize: ${err.message}`);
            this.isConnected = false;
            this.isInitialized = false;
            throw err;
        }
    }

    getInitialized() {
        return this.isInitialized;
    }

    getConnected() {
        return this.isConnected;
    }

    getStatus() {
        return this.lastStatus || { s: 'error', msg: 'Not initialized' };
    }

    async sendCommand(device, command, args = null) {
        if (!this.isInitialized) {
            return { s: 'error', msg: 'Pico not initialized' };
        }

        try {
            // Format: DEVICE:COMMAND[:ARGS]
            let fullCmd = `${device}:${command}`;
            if (args) {
                fullCmd += `:${args}`;
            }

            logger.debug(`[PICO-CMD] Sending: ${fullCmd}`);
            
            // Send via UART
            const response = await uartSerial.send(fullCmd);
            logger.debug(`[PICO-RES] Received: ${response}`);

            // Try to parse as JSON response
            try {
                return JSON.parse(response);
            } catch {
                // If not JSON, return as raw response
                return { s: 'ok', msg: response, raw: response };
            }
        } catch (err) {
            logger.error(`[PICO-ERR] Command failed: ${err.message}`);
            return { s: 'error', msg: err.message };
        }
    }

    async stop() {
        try {
            await uartSerial.close();
            this.isConnected = false;
            logger.info('[PICO] UART connection closed');
        } catch (err) {
            logger.error(`[PICO] Error closing connection: ${err.message}`);
        }
    }
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
        // Build allowed connect sources for socket.io and API calls
        const connectSources = [
            "'self'",
            "http://localhost:3000",
            "http://localhost:8080",
            "ws://localhost:3000",
            "wss://localhost:3000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080",
            "ws://127.0.0.1:3000",
            "wss://127.0.0.1:3000"
        ];
        
        // Add hostname-based connects
        if (this.hostname) {
            connectSources.push(`http://${this.hostname}:3000`);
            connectSources.push(`http://${this.hostname}:8080`);
            connectSources.push(`ws://${this.hostname}:3000`);
            connectSources.push(`http://${this.hostname}.local:3000`);
            connectSources.push(`http://${this.hostname}.local:8080`);
            connectSources.push(`ws://${this.hostname}.local:3000`);
        }

        // Security middleware with CSP for self-hosted resources only
        this.app.use(helmet({
            contentSecurityPolicy: {
                directives: {
                    defaultSrc: ["'self'"],
                    scriptSrc: ["'self'", "'unsafe-inline'"],
                    styleSrc: ["'self'", "'unsafe-inline'"],
                    connectSrc: connectSources,
                    fontSrc: ["'self'"],
                    imgSrc: ["'self'", "data:"],
                    mediaSrc: ["'self'"],
                    objectSrc: ["'none'"]
                    // Deliberately omit upgrade-insecure-requests
                }
            },
            crossOriginOpenerPolicy: false,
            originAgentCluster: false,
            hsts: false,  // Disable HSTS to allow HTTP
            referrerPolicy: { policy: 'no-referrer' }
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
        
        // Protocol consistency middleware - ensure no unwanted redirects and clear HTTPS upgrade policies
        this.app.use((req, res, next) => {
            // Set strict caching control to prevent HTTPS cached preferences
            res.setHeader('Cache-Control', 'public, max-age=600');
            res.setHeader('X-Forwarded-Proto', 'http');
            // Explicitly tell browser NOT to upgrade to HTTPS
            res.setHeader('X-Content-Type-Options', 'nosniff');
            // Remove any HSTS headers that might force HTTPS
            res.removeHeader('Strict-Transport-Security');
            // Ensure we're NOT sending CSP upgrade-insecure-requests
            const csp = res.getHeader('Content-Security-Policy');
            if (csp && csp.includes('upgrade-insecure-requests')) {
                const newCsp = csp.replace('upgrade-insecure-requests', '').replace(/;\s*;/g, ';').trim();
                res.setHeader('Content-Security-Policy', newCsp);
            }
            next();
        });
        
        // Serve static files from client build (both production and development)
        const clientDistPath = path.join(__dirname, '../client/dist');
        
        // Middleware for HTML files - ensure no HTTPS upgrade
        this.app.get('*.html', (req, res, next) => {
            res.set('Cache-Control', 'public, max-age=0, must-revalidate');
            res.set('Pragma', 'no-cache');
            res.set('Expires', '0');
            // Remove any CSP that might try to upgrade
            res.removeHeader('Content-Security-Policy');
            res.removeHeader('Content-Security-Policy-Report-Only');
            next();
        });
        
        this.app.use(express.static(clientDistPath, {
            maxAge: process.env.NODE_ENV === 'production' ? '1d' : 0,
            setHeaders: (res, path) => {
                // Force HTTP for HTML files, no caching of HTTPS preferences
                if (path.endsWith('.html')) {
                    res.set('Cache-Control', 'public, max-age=0, must-revalidate');
                    res.set('Pragma', 'no-cache');
                    res.set('Expires', '0');
                }
            }
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
        
        // Diagnostic dashboard
        this.app.get('/diagnostic', (req, res) => {
            const isRaspberryPi = process.platform === 'linux';
            const fs = require('fs');
            const uartAvailable = isRaspberryPi && fs.existsSync('/dev/ttyAMA0');
            
            const html = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Radar Server Diagnostic</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; }
        h1 { margin-bottom: 30px; color: #60a5fa; }
        h2 { margin-top: 20px; margin-bottom: 15px; color: #93c5fd; font-size: 1.2em; }
        .status { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; }
        .card-title { font-weight: bold; color: #60a5fa; margin-bottom: 10px; }
        .check { display: flex; justify-content: space-between; margin: 8px 0; font-size: 0.95em; }
        .label { color: #cbd5e1; }
        .value { color: #10b981; font-weight: bold; }
        .error { color: #ef4444; }
        .endpoint { background: #0f172a; padding: 10px; margin: 8px 0; border-left: 3px solid #60a5fa; border-radius: 4px; }
        a { color: #60a5fa; text-decoration: none; }
        a:hover { text-decoration: underline; }
        footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #334155; text-align: center; color: #64748b; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛰️ Radar Server Diagnostic</h1>
        
        <div class="status">
            <div class="card">
                <div class="card-title">Server Status</div>
                <div class="check"><span class="label">Uptime:</span><span class="value">${Math.floor(process.uptime())}s</span></div>
                <div class="check"><span class="label">Memory:</span><span class="value">${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB</span></div>
                <div class="check"><span class="label">Platform:</span><span class="value">${process.platform}</span></div>
            </div>
            <div class="card">
                <div class="card-title">Hardware</div>
                <div class="check"><span class="label">Raspberry Pi:</span><span class="value ${isRaspberryPi ? '' : 'error'}">${isRaspberryPi ? '✓ Yes' : '✗ No'}</span></div>
                <div class="check"><span class="label">UART:</span><span class="value ${uartAvailable ? '' : 'error'}">${uartAvailable ? '✓ Available' : '✗ Not available'}</span></div>
                <div class="check"><span class="label">Port 3000:</span><span class="value">✓ Open</span></div>
            </div>
        </div>
        
        <h2>API Endpoints</h2>
        <div class="endpoint"><a href="/api/status">GET /api/status</a> - Server status</div>
        <div class="endpoint"><a href="/api/health">GET /api/health</a> - Health check</div>
        <div class="endpoint"><a href="/api/diagnostic">GET /api/diagnostic</a> - JSON diagnostic data</div>
        <div class="endpoint"><a href="/">GET /</a> - Frontend application</div>
        
        <footer>
            <p>Server v${require('../package.json').version}</p>
            <p>${new Date().toLocaleString()}</p>
        </footer>
    </div>
</body>
</html>`;
            res.send(html);
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
                
                // Start background Pico reconnection attempts (retry every 60 seconds to reduce log noise)
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
        // Attempt to reconnect to Pico every 60 seconds (reduced from 10s to minimize log noise)
        this.picoReconnectInterval = setInterval(async () => {
            try {
                if (this.picoController?.initialize && !this.isConnected) {
                    logger.debug('Attempting to reconnect to Pico Master...');
                    await this.picoController.initialize();
                    logger.info('Pico controller reconnection/reinitialization attempted');
                }
            } catch (error) {
                // Only log at debug level to reduce noise
                logger.debug('Pico reconnection attempt failed, will retry...', error.message);
            }
        }, 60000);
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