const express = require('express');

/**
 * Create Stepper Motor Routes (GET and PUT/PUSH)
 * Base URL: /api/stepper
 */
function createStepperRoutes(stepperController) {
    const router = express.Router();
    
    // ============================================================
    // GET ENDPOINTS
    // ============================================================
    
    /**
     * GET /api/stepper/heartbeat
     * Returns heartbeat counter and uptime
     */
    router.get('/heartbeat', async (req, res) => {
        try {
            const result = await stepperController.getHeartbeat();
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
     * GET /api/stepper/speed
     * Returns current speed, min, and max values
     */
    router.get('/speed', async (req, res) => {
        try {
            const result = await stepperController.getSpeed();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/enable
     * Returns enabled state
     */
    router.get('/enable', async (req, res) => {
        try {
            const result = await stepperController.getEnabled();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/direction
     * Returns current direction (CW or CCW)
     */
    router.get('/direction', async (req, res) => {
        try {
            const result = await stepperController.getDirection();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/position
     * Returns current position in degrees and home status
     */
    router.get('/position', async (req, res) => {
        try {
            const result = await stepperController.getPosition();
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
     * GET /api/stepper/at-home
     * Returns whether stepper is at home position
     */
    router.get('/at-home', async (req, res) => {
        try {
            const result = await stepperController.getAtHome();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/current-speed
     * Returns current speed in microseconds
     */
    router.get('/current-speed', async (req, res) => {
        try {
            const result = await stepperController.getCurrentSpeed();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/home-calibrated
     * Returns calibration status
     */
    router.get('/home-calibrated', async (req, res) => {
        try {
            const result = await stepperController.getHomeCalibrated();
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
     * GET /api/stepper/continuous-rotating
     * Returns continuous rotation status and direction
     */
    router.get('/continuous-rotating', async (req, res) => {
        try {
            const result = await stepperController.getContinuousRotating();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/max-speed
     * Returns maximum speed limit
     */
    router.get('/max-speed', async (req, res) => {
        try {
            const result = await stepperController.getMaxSpeed();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/min-speed
     * Returns minimum speed limit
     */
    router.get('/min-speed', async (req, res) => {
        try {
            const result = await stepperController.getMinSpeed();
            res.json({ success: true, data: result.data });
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    /**
     * GET /api/stepper/sensor-state
     * Returns home sensor state (triggered or clear)
     */
    router.get('/sensor-state', async (req, res) => {
        try {
            const result = await stepperController.getSensorState();
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
     * GET /api/stepper/status
     * Returns complete system status
     */
    router.get('/status', async (req, res) => {
        try {
            const result = await stepperController.getStatus();
            if (result.success) {
                res.json({ success: true, data: result.data });
            } else {
                res.status(500).json(result);
            }
        } catch (error) {
            res.status(500).json({ success: false, error: error.message, code: 'SERVER_ERROR' });
        }
    });
    
    // ============================================================
    // PUT/PUSH ENDPOINTS (State Modification)
    // ============================================================
    
    /**
     * PUT /api/stepper/home
     * Find and calibrate home position
     */
    router.put('/home', async (req, res) => {
        try {
            const method = req.body.method || 'complete';
            const result = await stepperController.findHome(method);
            
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
     * PUT /api/stepper/move
     * Move to absolute angle
     * Body: { angle: <0-360> }
     */
    router.put('/move', async (req, res) => {
        try {
            const { angle } = req.body;
            const result = await stepperController.moveToAngle(angle);
            
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
     * PUT /api/stepper/rotate
     * Rotate by relative amount
     * Body: { degrees: <number> }
     */
    router.put('/rotate', async (req, res) => {
        try {
            const { degrees } = req.body;
            const result = await stepperController.rotateByDegrees(degrees);
            
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
     * PUT /api/stepper/speed
     * Set motor speed
     * Body: { speed: <500-10000> }
     */
    router.put('/speed', async (req, res) => {
        try {
            const { speed } = req.body;
            const result = await stepperController.setSpeed(speed);
            
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
     * PUT /api/stepper/enable
     * Enable or disable motor
     * Body: { enabled: <bool> }
     */
    router.put('/enable', async (req, res) => {
        try {
            const { enabled } = req.body;
            const result = await stepperController.setEnabled(enabled);
            
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
     * PUT /api/stepper/continuous
     * Start or stop continuous rotation
     * Body: { rotating: <bool>, direction: <"CW"|"CCW"|null> }
     */
    router.put('/continuous', async (req, res) => {
        try {
            const { rotating, direction } = req.body;
            
            let result;
            if (rotating) {
                result = await stepperController.startContinuousRotation(direction);
            } else {
                result = await stepperController.stopContinuousRotation();
            }
            
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
     * PUT /api/stepper/max-speed
     * Set maximum speed limit
     * Body: { maxSpeed: <microseconds> }
     */
    router.put('/max-speed', async (req, res) => {
        try {
            const { maxSpeed } = req.body;
            const result = await stepperController.setMaxSpeed(maxSpeed);
            
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
     * PUT /api/stepper/min-speed
     * Set minimum speed limit
     * Body: { minSpeed: <microseconds> }
     */
    router.put('/min-speed', async (req, res) => {
        try {
            const { minSpeed } = req.body;
            const result = await stepperController.setMinSpeed(minSpeed);
            
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

module.exports = createStepperRoutes;
