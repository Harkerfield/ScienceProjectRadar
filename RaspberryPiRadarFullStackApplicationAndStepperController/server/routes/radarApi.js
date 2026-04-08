const express = require('express');

/**
 * Create Radar Routes (GET only)
 * Base URL: /api/radar
 */
function createRadarRoutes(radarController) {
    const router = express.Router();
    
    // ============================================================
    // GET ENDPOINTS
    // ============================================================
    
    /**
     * GET /api/radar/values
     * Returns latest radar readings: distance, confidence, movement
     */
    router.get('/values', async (req, res) => {
        try {
            const result = await radarController.getValues();
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
     * GET /api/radar/status
     * Returns radar operational status and last readings
     */
    router.get('/status', async (req, res) => {
        try {
            const result = await radarController.getStatus();
            if (result.success) {
                res.json({ success: true, data: result.data });
            } else {
                res.status(500).json(result);
            }
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
}

module.exports = createRadarRoutes;
