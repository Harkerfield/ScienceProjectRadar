const express = require('express');
const os = require('os');
const createUnifiedDeviceRoutes = require('./deviceApi');

/**
 * Create API routes with device control integration
 * @param {SerialComm} serialComm - Serial communication handler
 * @param {Logger} logger - Logger instance
 * @returns {express.Router} Configured API router
 */
function createApiRoutes(serialComm, logger) {
    const router = express.Router();

// Root API discovery endpoint
router.get('/', (req, res) => {
    res.json({
        version: require('../package.json').version,
        name: 'Radar Control System API',
        description: 'RESTful API for controlling radar, stepper, and servo devices',
        baseUrl: `http://${req.hostname}:${process.env.PORT || 3000}`,
        sections: {
            '/api/status': 'Current server status',
            '/api/health': 'Health check',
            '/api/diagnostic': 'Detailed diagnostic information',
            '/api/device': 'Device control endpoints (GET to discover)',
            '/api/restart': 'Request system restart (POST)',
            '/api/shutdown': 'Request system shutdown (POST)'
        },
        documentation: {
            quickStart: 'GET /api/device to see available devices',
            devices: 'GET /api/device/:device to see available commands',
            sendCommand: 'POST /api/device/:device/:command',
            examples: {
                listAll: '/api/device/commands',
                listDevice: '/api/device/STEPPER/info',
                sendCommand: 'POST /api/device/STEPPER/SPIN with body {"args":{"speed_us":"1500"}}'
            }
        }
    });
});

// Comprehensive diagnostic endpoint
router.get('/diagnostic', (req, res) => {
    const diagnostic = {
        status: 'ok',
        timestamp: new Date().toISOString(),
        server: {
            version: require('../package.json').version,
            uptime: `${Math.floor(process.uptime())}s`,
            environment: process.env.NODE_ENV || 'development',
            platform: process.platform,
            nodeVersion: process.version,
            memory: {
                heapUsed: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`,
                heapTotal: `${Math.round(process.memoryUsage().heapTotal / 1024 / 1024)}MB`,
                external: `${Math.round(process.memoryUsage().external / 1024 / 1024)}MB`
            },
            cpu: {
                cores: os.cpus().length,
                loadAverage: os.loadavg()
            }
        },
        hardware: {
            isRaspberryPi: process.platform === 'linux',
            hostname: os.hostname(),
            arch: os.arch()
        },
        uart: {
            available: process.platform === 'linux' && require('fs').existsSync('/dev/ttyAMA0'),
            path: process.env.SERIAL_PORT || '/dev/ttyAMA0',
            baudRate: Number(process.env.BAUD_RATE || 460800),
            note: 'UART will only initialize on Raspberry Pi Linux'
        },
        endpoints: {
            'GET /api/status': 'Server status',
            'GET /api/health': 'Health check',
            'GET /api/diagnostic': 'This page',
            'POST /api/restart': 'Request system restart',
            'POST /api/shutdown': 'Request system shutdown'
        }
    };
    
    res.json(diagnostic);
});

// General system routes
router.get('/status', (req, res) => {
    res.json({
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: require('../package.json').version,
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        env: process.env.NODE_ENV || 'development'
    });
});

router.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        checks: {
            memory: process.memoryUsage().heapUsed < 500 * 1024 * 1024, // Less than 500MB
            uptime: process.uptime() > 0
        }
    });
});

router.post('/restart', (req, res) => {
    res.json({
        message: 'Restart signal sent',
        timestamp: new Date().toISOString()
    });
    
    // Emit restart event to server
    if (req.app.get('io')) {
        req.app.get('io').emit('system:restart');
    }
});

router.post('/shutdown', (req, res) => {
    res.json({
        message: 'Shutdown signal sent',
        timestamp: new Date().toISOString()
    });
    
    // Emit shutdown event to server
    if (req.app.get('io')) {
        req.app.get('io').emit('system:shutdown');
    }
});

// Microcontroller settings endpoints
router.get('/config/microcontroller-settings', (req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');
        const settingsPath = path.join(__dirname, '../config/microcontrollerSettings.json');
        
        if (!fs.existsSync(settingsPath)) {
            return res.status(404).json({
                success: false,
                error: 'Settings file not found',
                message: 'microcontrollerSettings.json does not exist'
            });
        }
        
        const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
        res.json({
            success: true,
            settings: settings
        });
    } catch (error) {
        logger.error('Error reading microcontroller settings:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to read settings',
            message: error.message
        });
    }
});

router.post('/config/microcontroller-settings', (req, res) => {
    try {
        const fs = require('fs');
        const path = require('path');
        const settingsPath = path.join(__dirname, '../config/microcontrollerSettings.json');
        
        if (!req.body || typeof req.body !== 'object') {
            return res.status(400).json({
                success: false,
                error: 'Invalid request',
                message: 'Request body must be a valid JSON object'
            });
        }
        
        // Add timestamp to metadata
        if (!req.body.metadata) {
            req.body.metadata = {};
        }
        req.body.metadata.lastModified = new Date().toISOString();
        
        fs.writeFileSync(settingsPath, JSON.stringify(req.body, null, 2), 'utf8');
        
        logger.info('Microcontroller settings updated');
        
        // Broadcast update to all connected clients
        if (req.app.get('io')) {
            req.app.get('io').emit('config:settings-updated', {
                timestamp: new Date().toISOString(),
                settings: req.body
            });
        }
        
        res.json({
            success: true,
            message: 'Settings updated successfully',
            lastModified: req.body.metadata.lastModified
        });
    } catch (error) {
        logger.error('Error saving microcontroller settings:', error);
        res.status(500).json({
            success: false,
            error: 'Failed to save settings',
            message: error.message
        });
    }
});

    // Mount unified device control API
    // This must be before the module.exports so routes are properly nested
    router.use('/device', createUnifiedDeviceRoutes(serialComm, logger));

    return router;
}

module.exports = createApiRoutes;