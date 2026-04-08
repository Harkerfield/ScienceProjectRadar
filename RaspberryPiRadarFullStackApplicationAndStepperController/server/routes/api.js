const express = require('express');
const router = express.Router();

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