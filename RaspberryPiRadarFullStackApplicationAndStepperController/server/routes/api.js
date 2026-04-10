const express = require('express');
const router = express.Router();
const os = require('os');

// Comprehensive diagnostic endpoint
router.get('/diagnostic', (req, res) => {
    const diagnostic = {
        status: 'ok',
        timestamp: new Date().toISOString(),
        server: {
            version: require('../../package.json').version,
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
        version: require('../../package.json').version,
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

module.exports = router;