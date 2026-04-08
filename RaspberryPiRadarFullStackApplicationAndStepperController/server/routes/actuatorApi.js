const express = require('express');

/**
 * Create Actuator Routes (GET and PUT/PUSH)
 * Base URL: /api/actuator
 */
function createActuatorRoutes(actuatorController) {
    const router = express.Router();
    
    // ============================================================
    // GET ENDPOINTS
    // ============================================================
    
    /**
     * GET /api/actuator/heartbeat
     * Returns actuator heartbeat counter
     */
    router.get('/heartbeat', async (req, res) => {
        try {
            const result = await actuatorController.getHeartbeat();
            if (result.success) {
                res.json({ success: true, data: result.data });
            } else {
                res.status(500).json(result);
            }
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/actuator/position
     * Returns actuator position and state
     */
    router.get('/position', async (req, res) => {
        try {
            const result = await actuatorController.getPosition();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/actuator/status
     * Returns complete actuator status
     */
    router.get('/status', async (req, res) => {
        try {
            const result = await actuatorController.getStatus();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    // ============================================================
    // PUT/PUSH ENDPOINTS (State Modification)
    // ============================================================
    
    /**
     * PUT /api/actuator/open
     * Open the actuator
     */
    router.put('/open', async (req, res) => {
        try {
            const result = await actuatorController.open();
            
            if (result.success) {
                res.json({ success: true, data: result.data });
            } else {
                res.status(400).json(result);
            }
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * PUT /api/actuator/close
     * Close the actuator
     */
    router.put('/close', async (req, res) => {
        try {
            const result = await actuatorController.close();
            
            if (result.success) {
                res.json({ success: true, data: result.data });
            } else {
                res.status(400).json(result);
            }
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * PUT /api/actuator/position
     * Set actuator to specific position
     * Body: { position: <0-100> }
     */
    router.put('/position', async (req, res) => {
        try {
            const { position } = req.body;
            const result = await actuatorController.setPosition(position);
            
            if (result.success) {
                res.json({ success: true, data: result.data });
            } else {
                res.status(400).json(result);
            }
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    return router;
}

module.exports = createActuatorRoutes;
