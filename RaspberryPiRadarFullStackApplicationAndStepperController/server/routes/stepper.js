const express = require('express');

function createStepperRoutes(stepperController) {
    const router = express.Router();
    
    // Get stepper status
    router.get('/status', (req, res) => {
        try {
            const status = stepperController.getStatus();
            res.json(status);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Start stepper motor
    router.post('/start', (req, res) => {
        try {
            const { speed, direction } = req.body;
            const success = stepperController.startRotation({ speed, direction });
            
            if (success) {
                res.json({
                    message: 'Stepper motor started',
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to start stepper motor' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Stop stepper motor
    router.post('/stop', (req, res) => {
        try {
            const success = stepperController.stopRotation();
            
            if (success) {
                res.json({
                    message: 'Stepper motor stopped',
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to stop stepper motor' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Set motor speed
    router.put('/speed', (req, res) => {
        try {
            const { speed } = req.body;
            
            if (typeof speed !== 'number' || speed < 1 || speed > 1000) {
                return res.status(400).json({ error: 'Speed must be a number between 1 and 1000' });
            }
            
            const success = stepperController.setRotationSpeed(speed);
            
            if (success) {
                res.json({
                    message: 'Speed updated',
                    speed: speed,
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to set speed' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Set motor direction
    router.put('/direction', (req, res) => {
        try {
            const { direction } = req.body;
            
            if (typeof direction !== 'number' || (direction !== 1 && direction !== -1)) {
                return res.status(400).json({ error: 'Direction must be 1 (clockwise) or -1 (counterclockwise)' });
            }
            
            const success = stepperController.setDirection(direction);
            
            if (success) {
                res.json({
                    message: 'Direction updated',
                    direction: direction,
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to set direction' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Manual step control
    router.post('/step', (req, res) => {
        try {
            const { steps = 1, direction = 1 } = req.body;
            
            if (stepperController.isRunning) {
                return res.status(400).json({ error: 'Cannot step while motor is running continuously' });
            }
            
            let success;
            if (direction > 0) {
                success = stepperController.stepForward(steps);
            } else {
                success = stepperController.stepBackward(steps);
            }
            
            if (success) {
                res.json({
                    message: `Stepped ${steps} steps ${direction > 0 ? 'forward' : 'backward'}`,
                    steps: steps,
                    direction: direction,
                    timestamp: new Date().toISOString()
                });
            } else {
                res.status(400).json({ error: 'Failed to step motor' });
            }
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Reset step counter
    router.post('/reset', (req, res) => {
        try {
            stepperController.resetStepCount();
            res.json({
                message: 'Step count reset to zero',
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    // Get motor configuration
    router.get('/config', (req, res) => {
        try {
            const status = stepperController.getStatus();
            res.json(status.config);
        } catch (error) {
            res.status(500).json({ error: error.message });
        }
    });
    
    return router;
}

module.exports = createStepperRoutes;