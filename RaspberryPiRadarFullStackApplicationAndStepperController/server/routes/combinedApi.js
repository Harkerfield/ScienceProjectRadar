const express = require('express');

/**
 * Create Combined Routes
 * Base URL: /api/combined
 * For endpoints that combine data from multiple sources
 */
function createCombinedRoutes(stepperController, radarController) {
    const router = express.Router();
    
    /**
     * GET /api/combined/stepper-radar
     * Returns combined stepper position + radar values in a single request
     * Useful for UI updates that need both datasets
     */
    router.get('/stepper-radar', async (req, res) => {
        try {
            // Get stepper position concurrently
            const stepperResult = await stepperController.getPosition();
            
            // Get radar values concurrently
            const radarResult = await radarController.getValues();
            
            if (stepperResult.success && radarResult.success) {
                res.json({
                    success: true,
                    data: {
                        stepper: {
                            position: stepperResult.data.position,
                            atHome: stepperResult.data.atHome,
                            calibrated: stepperResult.data.calibrated
                        },
                        radar: {
                            distance: radarResult.data.distance,
                            confidence: radarResult.data.confidence,
                            movement: radarResult.data.movement
                        },
                        timestamp: Date.now()
                    }
                });
            } else {
                const errors = [];
                if (!stepperResult.success) errors.push(`Stepper: ${stepperResult.error}`);
                if (!radarResult.success) errors.push(`Radar: ${radarResult.error}`);
                
                res.status(500).json({
                    success: false,
                    error: errors.join('; '),
                    code: 'DEVICE_ERROR'
                });
            }
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'SERVER_ERROR'
            });
        }
    });
    
    /**
     * GET /api/combined/system-status
     * Returns complete system status: stepper + actuator + radar
     */
    router.get('/system-status', async (req, res) => {
        try {
            // These could be made optional parameters if needed
            const stepperResult = await stepperController.getStatus();
            const radarResult = await radarController.getStatus();
            
            if (stepperResult.success && radarResult.success) {
                res.json({
                    success: true,
                    data: {
                        stepper: stepperResult.data,
                        radar: radarResult.data,
                        timestamp: Date.now()
                    }
                });
            } else {
                const errors = [];
                if (!stepperResult.success) errors.push(`Stepper: ${stepperResult.error}`);
                if (!radarResult.success) errors.push(`Radar: ${radarResult.error}`);
                
                res.status(500).json({
                    success: false,
                    error: errors.join('; '),
                    code: 'DEVICE_ERROR'
                });
            }
        } catch (error) {
            res.status(500).json({
                success: false,
                error: error.message,
                code: 'SERVER_ERROR'
            });
        }
    });
    
    return router;
}

module.exports = createCombinedRoutes;
