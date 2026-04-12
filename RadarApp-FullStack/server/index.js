const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
const os = require('os');
require('dotenv').config();

const logger = require('./utils/logger');
const SerialComm = require('./utils/SerialComm');

// Routes
const apiRoutes = require('./routes/api');

class RadarFullStackServer {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        
        // Network configuration
        this.hostname = os.hostname();
        this.corsOrigins = this.getCorsOrigins();
        
        this.io = socketIo(this.server, {
            cors: {
                origin: this.corsOrigins,
                methods: ["GET", "POST"],
                credentials: true
            }
        });
        
        this.port = process.env.PORT ||3000;
        
        // Initialize serial communication
        this.serialComm = new SerialComm({
            pythonExe: process.env.PYTHON_EXE || 'python3',
            scriptPath: path.join(__dirname, '../serial_bridge.py'),
            commandTimeout: 5000
        });
        
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
        
        if (this.hostname) {
            origins.push(`http://${this.hostname}:3000`);
            origins.push(`http://${this.hostname}:8080`);
            origins.push(`http://${this.hostname}.local:3000`);
            origins.push(`http://${this.hostname}.local:8080`);
        }
        
        return origins.filter(o => o && o.length > 0);
    }
    
    setupMiddleware() {
        // Prevent any HTTPS upgrade attempts - explicitly allow HTTP for local network
        this.app.use((req, res, next) => {
            res.removeHeader('Strict-Transport-Security');
            res.setHeader('X-Content-Type-Options', 'nosniff');
            next();
        });

        // Security - relaxed for local network HTTP access (DISABLE CSP from helmet)
        this.app.use(helmet({
            contentSecurityPolicy: false,  // Disable helmet's CSP
            hsts: false,
            referrerPolicy: { policy: 'no-referrer' },
            crossOriginOpenerPolicy: false,
            crossOriginResourcePolicy: false,
            originAgentCluster: false
        }));

        // CRITICAL: Remove upgrade-insecure-requests if helmet added it anyway
        // This must run AFTER helmet middleware
        this.app.use((req, res, next) => {
            const originalSetHeader = res.setHeader;
            res.setHeader = function(name, value) {
                if (name.toLowerCase() === 'content-security-policy' && typeof value === 'string') {
                    // Remove upgrade-insecure-requests directive
                    value = value.replace(/;?upgrade-insecure-requests/g, '');
                    // Remove any trailing semicolons
                    value = value.replace(/;+$/, '');
                }
                return originalSetHeader.call(this, name, value);
            };
            next();
        });

        // Set clean manual CSP without upgrade-insecure-requests
        this.app.use((req, res, next) => {
            const cspDirectives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline'",
                "style-src 'self' 'unsafe-inline'",
            `connect-src ${this.getConnectSources(req).join(' ')}`,
                "media-src 'self'",
                "object-src 'none'",
                "base-uri 'self'",
                "font-src 'self' https: data:",
                "form-action 'self'",
                "frame-ancestors 'self'",
                "img-src 'self' data:",
                "script-src-attr 'none'"
            ];
            res.setHeader('Content-Security-Policy', cspDirectives.join(';'));
            next();
        });
        
        // CORS - Permissive for local network development
        this.app.use(cors({
            origin: true,  // Allow all origins
            credentials: true,
            methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            allowedHeaders: ['Content-Type', 'Authorization'],
            optionsSuccessStatus: 200
        }));
        
        // Body parsing
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));
        
        // Logging
        this.app.use((req, res, next) => {
            logger.info(`${req.method} ${req.url} - ${req.ip}`);
            next();
        });
        
        // Static files
        const clientDistPath = path.join(__dirname, '../client/dist');
        this.app.use(express.static(clientDistPath, {
            maxAge: process.env.NODE_ENV === 'production' ? '1d' : 0
        }));
        logger.info(`Serving static files from: ${clientDistPath}`);
    }
    
    getConnectSources(req = null) {
        const sources = new Set([
            "'self'",
            "http://localhost:3000",
            "http://localhost:8080",
            "ws://localhost:3000",
            "wss://localhost:3000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8080"
        ]);

        // Allow connect-src for all detected local IPv4 interfaces.
        const interfaces = os.networkInterfaces();
        for (const iface of Object.values(interfaces)) {
            if (!iface) continue;
            for (const addr of iface) {
                if (addr.family !== 'IPv4' || addr.internal) continue;
                sources.add(`http://${addr.address}:3000`);
                sources.add(`http://${addr.address}:8080`);
                sources.add(`ws://${addr.address}:3000`);
            }
        }

        // Include the current request host if available (for LAN debugging via IP).
        if (req && typeof req.get === 'function') {
            const hostHeader = req.get('host') || '';
            const hostOnly = hostHeader.split(':')[0];
            if (hostOnly) {
                sources.add(`http://${hostOnly}:3000`);
                sources.add(`http://${hostOnly}:8080`);
                sources.add(`ws://${hostOnly}:3000`);
            }
        }
        
        if (this.hostname) {
            sources.add(`http://${this.hostname}:3000`);
            sources.add(`http://${this.hostname}:8080`);
            sources.add(`ws://${this.hostname}:3000`);
            sources.add(`http://${this.hostname}.local:3000`);
            sources.add(`http://${this.hostname}.local:8080`);
            sources.add(`ws://${this.hostname}.local:3000`);
        }
        
        return Array.from(sources);
    }
    
    setupRoutes() {
        // Root discovery endpoint
        this.app.get('/', (req, res) => {
            const getUrl = (path) => {
                const protocol = req.protocol || 'http';
                const host = req.get('host') || 'localhost';
                return `${protocol}://${host}${path}`;
            };

            res.json({
                name: 'Radar Control System',
                version: require('../package.json').version,
                status: 'running',
                timestamp: new Date().toISOString(),
                sections: {
                    api: {
                        description: 'RESTful API for device control',
                        discover: getUrl('/api'),
                        endpoints: {
                            'GET /api/device': 'Device control system',
                            'GET /api/status': 'Server status',
                            'GET /api/health': 'Health check',
                            'GET /api/diagnostic': 'Diagnostics'
                        }
                    },
                    ui: {
                        description: 'Web dashboard',
                        url: getUrl('/'),
                        client: 'Vue.js single-page application'
                    },
                    websocket: {
                        description: 'Real-time updates via Socket.io',
                        url: getUrl('/'),
                        port: process.env.PORT || 3000
                    }
                },
                getting_started: 'GET /api for device control API',
                shortcuts: {
                    listDevices: getUrl('/api/device'),
                    listCommands: getUrl('/api/device/commands'),
                    serverStatus: getUrl('/api/status'),
                    diagnostic: getUrl('/api/diagnostic')
                }
            });
        });

        // API routes
        this.app.use('/api', apiRoutes(this.serialComm, logger));

        // Health check endpoint
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'ok',
                timestamp: new Date().toISOString(),
                uptime: process.uptime(),
                serial: {
                    connected: this.serialComm?.isConnected || false
                }
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
                <div class="check"><span class="label">Serial Bridge:</span><span class="value ${this.serialComm?.isConnected ? '' : 'error'}">${this.serialComm?.isConnected ? '✓ Connected' : '✗ Disconnected'}</span></div>
            </div>
        </div>
        
        <h2>Unified Device API</h2>
        <div class="endpoint"><a href="/api/device/commands">GET /api/device/commands</a> - All available device commands</div>
        <div class="endpoint"><a href="/api/device/STEPPER/info">GET /api/device/STEPPER/info</a> - Stepper commands</div>
        <div class="endpoint"><a href="/api/device/RADAR/info">GET /api/device/RADAR/info</a> - Radar commands</div>
        <div class="endpoint"><a href="/api/device/ACTUATOR/info">GET /api/device/ACTUATOR/info</a> - Actuator commands</div>
        <div class="endpoint">POST /api/device/STEPPER/START - Send command (requires args in body)</div>
        
        <footer>
            <p>Server v${require('../package.json').version}</p>
            <p>${new Date().toLocaleString()}</p>
        </footer>
    </div>
</body>
</html>`;
            res.send(html);
        });
        
        // API discovery for /api/* paths that don't match
        this.app.use('/api', (req, res) => {
            res.status(404).json({
                success: false,
                error: `Endpoint not found: ${req.method} ${req.url}`,
                code: 'NOT_FOUND',
                availableEndpoints: {
                    'GET /api': 'API discovery',
                    'GET /api/device': 'Device control discovery',
                    'GET /api/device/:device': 'Device-specific commands',
                    'GET /api/device/:device/info': 'Device command specifications',
                    'POST /api/device/:device/:command': 'Send command to device',
                    'GET /api/device/commands': 'All device commands',
                    'GET /api/status': 'Server status',
                    'GET /api/health': 'Health check',
                    'GET /api/diagnostic': 'Detailed diagnostics',
                    'POST /api/restart': 'Restart system',
                    'POST /api/shutdown': 'Shutdown system'
                },
                hint: 'Start with GET /api to explore available endpoints',
                requestedPath: req.url,
                method: req.method
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
            const picoConnected = this.serialComm?.isConnected || false;
            socket.emit('system:status', {
                timestamp: new Date().toISOString(),
                serial: {
                    connected: picoConnected
                },
                pico: {
                    status: picoConnected ? 'ready' : 'unavailable',
                    initialized: picoConnected,
                    connected: picoConnected
                },
                system: {
                    uptime: process.uptime()
                }
            });
            
            // Generic device command handler
            socket.on('device:command', async (data) => {
                try {
                    const { device, command, args } = data;
                    logger.info(`Device command from ${socket.id}: ${device}:${command}`);
                    
                    const fullCommand = args 
                        ? `${device}:${command}:${args}`
                        : `${device}:${command}`;
                    
                    const response = await this.serialComm.sendDeviceCommand(fullCommand);
                    socket.emit('device:response', { device, command, response });
                    
                } catch (error) {
                    logger.error(`Device command error: ${error.message}`);
                    socket.emit('device:error', { error: error.message });
                }
            });
            
            // Stepper motor control
            socket.on('stepper:command', async (data) => {
                try {
                    logger.info(`Stepper command from ${socket.id}:`, data);
                    const { command, args } = data;
                    const fullCommand = args
                        ? `STEPPER:${command}:${args}`
                        : `STEPPER:${command}`;
                    
                    const response = await this.serialComm.sendDeviceCommand(fullCommand);
                    socket.emit('stepper:response', response);
                } catch (error) {
                    logger.error(`Stepper command error: ${error.message}`);
                    socket.emit('stepper:error', { error: error.message });
                }
            });
            
            // Radar control
            socket.on('radar:command', async (data) => {
                try {
                    logger.info(`Radar command from ${socket.id}:`, data);
                    const { command, args } = data;
                    const fullCommand = args
                        ? `RADAR:${command}:${args}`
                        : `RADAR:${command}`;
                    
                    const response = await this.serialComm.sendDeviceCommand(fullCommand);
                    socket.emit('radar:response', response);
                } catch (error) {
                    logger.error(`Radar command error: ${error.message}`);
                    socket.emit('radar:error', { error: error.message });
                }
            });
            
            // Actuator/Servo control
            socket.on('actuator:command', async (data) => {
                try {
                    logger.info(`Servo command from ${socket.id}:`, data);
                    const { command, args } = data;
                    const fullCommand = args
                        ? `SERVO:${command}:${args}`
                        : `SERVO:${command}`;
                    
                    const response = await this.serialComm.sendDeviceCommand(fullCommand);
                    socket.emit('actuator:response', response);
                } catch (error) {
                    logger.error(`Servo command error: ${error.message}`);
                    socket.emit('actuator:error', { error: error.message });
                }
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
            // Initialize device controllers and register their routes
            await this.initializeDeviceControllers();
            
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
            });
            
        } catch (error) {
            logger.error('Failed to start server:', error);
            process.exit(1);
        }
    }
    
    async initializeDeviceControllers() {
        try {
            // Initialize SerialComm connection to Python serial_bridge subprocess
            await this.serialComm.initialize();
            logger.info('SerialComm connection established');
            
            // Register callback for unsolicited serial data (e.g., radar continuous stream)
            this.serialComm.onSerialData((data) => {
                logger.debug('Received unsolicited serial data:', data);
                this.io.emit('serial:data', data);
            });
            
            logger.info('Device communication ready - unified API active');
            
        } catch (error) {
            logger.warn('Failed to initialize device controllers:', error.message);
            logger.warn('Devices will not be available');
            // Don't throw - allow server to continue without device controllers
        }
    }
    
    startStatusBroadcast() {
        // Broadcast system status every 5 seconds
        this.statusInterval = setInterval(() => {
            const picoConnected = this.serialComm?.isConnected || false;
            const status = {
                timestamp: new Date().toISOString(),
                serial: {
                    connected: picoConnected
                },
                pico: {
                    status: picoConnected ? 'ready' : 'unavailable',
                    initialized: picoConnected,
                    connected: picoConnected
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
            // Close and reinitialize SerialComm
            if (this.serialComm?.close) {
                await this.serialComm.close();
                logger.info('SerialComm closed');
            }
            
            // Reinitialize
            await this.initializeDeviceControllers();
            
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
            // Close SerialComm
            if (this.serialComm?.close) {
                await this.serialComm.close();
                logger.info('SerialComm closed');
            }
            
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