const logger = require('../utils/logger');

/**
 * PicoRadarController
 * Handles communication with Radar Pico slave via UART
 * Parses continuous data stream format: distance,confidence,movement\r\n
 */
class PicoRadarController {
    constructor(serialComm) {
        this.serialComm = serialComm;
        
        // Cache state
        this.state = {
            distance: 0,      // cm
            confidence: 0,    // 0-100
            movement: false,  // bool
            lastRead: 0,      // timestamp
            isActive: false
        };
    }
    
    /**
     * GET ENDPOINTS
     */
    
    async getValues() {
        try {
            return {
                success: true,
                data: {
                    distance: this.state.distance,
                    confidence: this.state.confidence,
                    movement: this.state.movement,
                    timestamp: this.state.lastRead
                }
            };
        } catch (error) {
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    async getStatus() {
        try {
            return {
                success: true,
                data: {
                    lastRead: this.state.lastRead,
                    isActive: this.state.isActive,
                    lastDistance: this.state.distance,
                    lastConfidence: this.state.confidence,
                    lastMovement: this.state.movement
                }
            };
        } catch (error) {
            return this._errorResponse(error.message, 'DEVICE_ERROR');
        }
    }
    
    /**
     * Parse radar data stream
     * Format: distance,confidence,movement\r\n
     * Example: 500,85,0\r\n (500cm, 85% confidence, no movement)
     */
    parseRadarData(dataLine) {
        try {
            const parts = dataLine.trim().split(',');
            if (parts.length !== 3) {
                logger.warn('Invalid radar data format:', dataLine);
                return null;
            }
            
            const distance = parseInt(parts[0]);
            const confidence = parseInt(parts[1]);
            const movement = parseInt(parts[2]) === 1;
            
            // Validate values
            if (isNaN(distance) || isNaN(confidence)) {
                logger.warn('Invalid radar values:', parts);
                return null;
            }
            
            if (confidence < 0 || confidence > 100) {
                logger.warn('Invalid confidence value:', confidence);
            }
            
            return {
                distance,
                confidence: Math.min(100, Math.max(0, confidence)),
                movement,
                timestamp: Date.now()
            };
        } catch (error) {
            logger.error('Error parsing radar data:', error);
            return null;
        }
    }
    
    /**
     * Update cached state with new radar reading
     */
    updateState(data) {
        if (data && this.isValidRadarData(data)) {
            this.state.distance = data.distance;
            this.state.confidence = data.confidence;
            this.state.movement = data.movement;
            this.state.lastRead = data.timestamp;
            this.state.isActive = true;
            return true;
        }
        return false;
    }
    
    isValidRadarData(data) {
        return data &&
               typeof data.distance === 'number' &&
               typeof data.confidence === 'number' &&
               typeof data.movement === 'boolean';
    }
    
    /**
     * HELPER METHODS
     */
    
    _errorResponse(message, code = 'ERROR') {
        return {
            success: false,
            error: message,
            code: code,
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = PicoRadarController;
