const express = require('express');

function createRadarRoutes(radarController) {
    const router = express.Router();
    
    // Get radar status
    router.get('/status', (req, res) => {
        try {
            const status = radarController.getStatus();
            res.json(status);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Start radar scanning
    router.post('/start', (req, res) => {
        try {
            const success = radarController.startScanning();
            
            if (success) {
                res.json({
                    message: 'Radar scanning started',
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to start radar scanning' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Stop radar scanning
    router.post('/stop', (req, res) => {
        try {
            const success = radarController.stopScanning();
            
            if (success) {
                res.json({
                    message: 'Radar scanning stopped',
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to stop radar scanning' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get recent radar data
    router.get('/data', (req, res) => {
        try {
            const count = parseInt(req.query.count) || 100;
            const data = radarController.getRecentData(count);
            
            res.json({
                data: data,
                totalPoints: data.length,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get radar statistics
    router.get('/stats', (req, res) => {
        try {
            const status = radarController.getStatus();
            res.json(status.stats);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Update radar configuration
    router.put('/config', (req, res) => {
        try {
            const newConfig = req.body;
            
            // Validate configuration
            if (newConfig.scanInterval && (newConfig.scanInterval < 10 || newConfig.scanInterval > 10000)) {
                return res.status(400).json({ error: 'scanInterval must be between 10 and 10000 ms' });
            }
            
            if (newConfig.detectionThreshold && (newConfig.detectionThreshold < 0 || newConfig.detectionThreshold > 100)) {
                return res.status(400).json({ error: 'detectionThreshold must be between 0 and 100' });
            }
            
            const success = radarController.updateConfiguration(newConfig);
            
            if (success) {
                res.json({
                    message: 'Configuration updated',
                    config: radarController.getStatus().config,
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to update configuration' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get current configuration
    router.get('/config', (req, res) => {
        try {
            const status = radarController.getStatus();
            res.json(status.config);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Clear radar data
    router.delete('/data', (req, res) => {
        try {
            radarController.clearData();
            res.json({
                message: 'Radar data cleared',
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Send command to radar module
    router.post('/command', (req, res) => {
        try {
            const { command } = req.body;
            
            if (!command || typeof command !== 'string') {
                return res.status(400).json({ error: 'Command is required and must be a string' });
            }
            
            radarController.sendCommand(command);
            
            res.json({
                message: 'Command sent to radar module',
                command: command,
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get radar data in different formats
    router.get('/data/csv', (req, res) => {
        try {
            const count = parseInt(req.query.count) || 100;
            const data = radarController.getRecentData(count);
            
            // Convert to CSV format
            const csvHeader = 'timestamp,distance,velocity,signalStrength,detected,angle,quality\n';
            const csvRows = data.map(point => 
                `${point.timestamp},${point.distance},${point.velocity},${point.signalStrength},${point.detected},${point.angle},${point.quality}`
            ).join('\n');
            
            const csv = csvHeader + csvRows;
            
            res.setHeader('Content-Type', 'text/csv');
            res.setHeader('Content-Disposition', 'attachment; filename="radar_data.csv"');
            res.send(csv);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Export radar data for analysis
    router.get('/export', (req, res) => {
        try {
            const status = radarController.getStatus();
            const data = radarController.getRecentData();
            
            const exportData = {
                exportTime: new Date().toISOString(),
                radarStatus: status,
                dataPoints: data,
                summary: {
                    totalPoints: data.length,
                    detections: data.filter(d => d.detected).length,
                    timespan: data.length > 0 ? {
                        start: data[0].timestamp,
                        end: data[data.length - 1].timestamp
                    } : null
                }
            };
            
            res.json(exportData);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    return router;
}

module.exports = createRadarRoutes;