const express = require('express');

function createPicoRoutes(picoController) {
    const router = express.Router();
    
    // Get Pico status
    router.get('/status', (req, res) => {
        try {
            const status = picoController.getStatus();
            res.json(status);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Send command to Pico
    router.post('/command', (req, res) => {
        try {
            const { command, params = {} } = req.body;
            
            if (!command) {
                return res.status(400).json({ error: 'Command is required' });
            }
            
            picoController.sendCommand(command, params);
            
            res.json({
                message: 'Command sent to Pico',
                command,
                params,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Request status from Pico
    router.post('/request-status', (req, res) => {
        try {
            picoController.requestStatus();
            
            res.json({
                message: 'Status request sent to Pico',
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Control servo via Pico
    router.post('/servo/:action', (req, res) => {
        try {
            const action = req.params.action;
            
            if (!['activate', 'deactivate'].includes(action)) {
                return res.status(400).json({ error: 'Action must be "activate" or "deactivate"' });
            }
            
            picoController.controlServo(action);
            
            res.json({
                message: `Servo ${action} command sent to Pico`,
                action,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Configure radar via Pico
    router.put('/radar/config', (req, res) => {
        try {
            const config = req.body;
            
            picoController.configureRadar(config);
            
            res.json({
                message: 'Radar configuration sent to Pico',
                config,
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get recent radar data from Pico
    router.get('/radar/data', (req, res) => {
        try {
            const count = parseInt(req.query.count) || 100;
            const data = picoController.getRecentRadarData(count);
            
            res.json({
                data,
                count: data.length,
                source: 'pico',
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get servo status from Pico
    router.get('/servo/status', (req, res) => {
        try {
            const status = picoController.getServoStatus();
            
            res.json({
                status,
                source: 'pico',
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get system information from Pico
    router.get('/system/info', (req, res) => {
        try {
            const info = picoController.getSystemInfo();
            
            res.json({
                info,
                source: 'pico',
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Send ping to Pico
    router.post('/ping', (req, res) => {
        try {
            picoController.sendPing();
            
            res.json({
                message: 'Ping sent to Pico',
                timestamp: new Date().toISOString()
            });
            
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    return router;
}

module.exports = createPicoRoutes;