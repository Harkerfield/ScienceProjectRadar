const PicoMasterSerial = require('../utils/picoMasterSerial');
const logger = require('../utils/logger');

class RadarController {
    constructor(io) {
        this.io = io;
        this.picoMaster = PicoMasterSerial.getInstance();
        this.isScanning = false;
        this.initialized = false;
        this.radarData = [];
        this.scanningInterval = null;
        
        // Radar configuration
        this.config = {
            scanInterval: 200, // milliseconds between reads
            maxDataPoints: 1000, // Maximum stored data points
            detectionThreshold: 50, // Signal strength threshold for detection
            filteringEnabled: true,
            averagingWindow: 5 // Number of readings to average
        };
        
        // Detection statistics
        this.stats = {
            totalScans: 0,
            detectionsCount: 0,
            lastDetection: null,
            averageSignalStrength: 0,
            maxDistance: 0,
            minDistance: Infinity,
            maxVelocity: 0
        };
        
        logger.info('Radar controller created');
    }
    
    async initialize() {
        try {
            logger.info('Initializing radar controller...');
            
            // Check if Pico Master is available
            if (!this.picoMaster || !this.picoMaster.isConnected()) {
                logger.warn('Pico Master not connected. Radar will initialize when available.');
                this.initialized = false;
                return;
            }
            
            // Test radar connection by sending PING command
            try {
                const response = await this.picoMaster.sendCommand('RADAR', 'PING');
                logger.info('Radar PING response:', response);
                this.initialized = true;
                
                this.io.emit('radar:initialized', {
                    config: this.config,
                    status: this.getStatus()
                });
                
            } catch (error) {
                logger.warn('Radar not responding to PING:', error.message);
                this.initialized = false;
                this.io.emit('radar:error', { 
                    message: 'Radar module not responding',
                    details: error.message 
                });
            }
            
        } catch (error) {
            logger.error('Error initializing radar controller:', error);
            throw error;
        }
    }
    
    processRadarData(rawData) {
        try {
            const timestamp = new Date().toISOString();
            const parsedData = this.parseRadarReading(rawData, timestamp);
            
            // Add to data array
            this.radarData.push(parsedData);
            
            // Limit stored data points
            if (this.radarData.length > this.config.maxDataPoints) {
                this.radarData = this.radarData.slice(-this.config.maxDataPoints);
            }
            
            // Update statistics
            this.updateStatistics(parsedData);
            
            // Apply filtering if enabled
            const filteredData = this.config.filteringEnabled ? 
                this.applyFiltering(parsedData) : parsedData;
            
            // Emit real-time data
            this.io.emit('radar:data', filteredData);
            
            // Check for detections
            if (filteredData.detected) {
                this.handleDetection(filteredData);
            }
            
        } catch (error) {
            logger.error('Error processing radar data:', error);
        }
    }
    
    parseRadarReading(rawData, timestamp) {
        // Parse RADAR protocol response: OK:range=123:velocity=4.5:confidence=75:movement=1
        
        const data = {
            timestamp: timestamp,
            raw: rawData.trim(),
            range: 0,
            distance: 0,
            velocity: 0,
            signalStrength: 0,
            confidence: 0,
            detected: false,
            movement: false,
            quality: 0
        };
        
        try {
            // Expected format: RADAR:OK:range=123:velocity=4.5:confidence=75:movement=1
            const parts = rawData.split(':');
            
            if (parts.length < 2) {
                logger.warn('Invalid radar data format:', rawData);
                return data;
            }
            
            // Skip RADAR device name and OK/ERROR status
            for (let i = 2; i < parts.length; i++) {
                const [key, value] = parts[i].split('=');
                const numValue = parseFloat(value) || parseInt(value);
                
                switch (key ? key.trim().toUpperCase() : '') {
                    case 'RANGE':
                        data.range = numValue;
                        data.distance = numValue; // Alias for API
                        break;
                    case 'VELOCITY':
                    case 'VEL':
                        data.velocity = numValue;
                        break;
                    case 'CONFIDENCE':
                    case 'CONF':
                        data.confidence = numValue;
                        data.signalStrength = numValue; // Alias for API
                        break;
                    case 'MOVEMENT':
                    case 'MOVE':
                        data.movement = Boolean(numValue);
                        break;
                    case 'QUALITY':
                    case 'QUAL':
                        data.quality = numValue;
                        break;
                }
            }
            
            // Determine detection based on confidence and range
            data.detected = data.confidence > this.config.detectionThreshold && data.range > 0 && data.range < 1000;
            
        } catch (error) {
            logger.warn('Error parsing radar data:', rawData, error);
        }
        
        return data;
    }
    
    applyFiltering(data) {
        // Apply moving average filter
        if (this.radarData.length >= this.config.averagingWindow) {
            const recentData = this.radarData.slice(-this.config.averagingWindow);
            
            data.distance = recentData.reduce((sum, d) => sum + d.distance, 0) / recentData.length;
            data.signalStrength = recentData.reduce((sum, d) => sum + d.signalStrength, 0) / recentData.length;
            data.velocity = recentData.reduce((sum, d) => sum + d.velocity, 0) / recentData.length;
        }
        
        // Apply detection threshold
        data.detected = data.signalStrength > this.config.detectionThreshold;
        
        return data;
    }
    
    updateStatistics(data) {
        this.stats.totalScans++;
        
        if (data.detected || data.confidence > 0) {
            this.stats.detectionsCount++;
            this.stats.lastDetection = data.timestamp;
            
            if (data.range > 0) {
                this.stats.maxDistance = Math.max(this.stats.maxDistance, data.range);
                this.stats.minDistance = Math.min(this.stats.minDistance, data.range);
            }
            
            // Track max velocity
            if (Math.abs(data.velocity) > Math.abs(this.stats.maxVelocity)) {
                this.stats.maxVelocity = data.velocity;
            }
        }
        
        // Update average signal strength (rolling average)
        const alpha = 0.1; // Smoothing factor
        this.stats.averageSignalStrength = 
            this.stats.averageSignalStrength * (1 - alpha) + (data.confidence || data.signalStrength || 0) * alpha;
    }
    
    handleDetection(data) {
        logger.info(`Motion detected: distance=${data.distance}cm, strength=${data.signalStrength}`);
        
        this.io.emit('radar:detection', {
            ...data,
            detectionId: `det_${Date.now()}`,
            confidence: this.calculateConfidence(data)
        });
    }
    
    calculateConfidence(data) {
        // Calculate detection confidence based on signal strength and data quality
        let confidence = 0;
        
        if (data.signalStrength > this.config.detectionThreshold) {
            confidence = Math.min(100, (data.signalStrength / 100) * 100);
        }
        
        // Adjust based on distance (closer = higher confidence)
        if (data.distance > 0 && data.distance < 500) {
            const distanceFactor = 1 - (data.distance / 500);
            confidence *= (0.7 + 0.3 * distanceFactor);
        }
        
        return Math.round(confidence);
    }
    
    startScanning() {
        if (!this.initialized) {
            const error = 'Radar not initialized';
            logger.error(error);
            this.io.emit('radar:error', { message: error });
            return false;
        }
        
        if (this.isScanning) {
            logger.warn('Radar is already scanning');
            return true;
        }
        
        try {
            this.isScanning = true;
            
            // Start periodic scanning - continuously read from radar
            this.scanningInterval = setInterval(async () => {
                if (this.isScanning) {
                    try {
                        // Send READ command to radar
                        const response = await this.picoMaster.sendCommand('RADAR', 'READ');
                        
                        if (response && response.startsWith('OK:')) {
                            this.processRadarData(response);
                        } else if (response && response.startsWith('ERROR:')) {
                            logger.warn('Radar error response:', response);
                        }
                    } catch (error) {
                        logger.warn('Error reading radar:', error.message);
                    }
                }
            }, this.config.scanInterval);
            
            logger.info('Started radar scanning');
            
            this.io.emit('radar:scanStarted', {
                interval: this.config.scanInterval,
                timestamp: new Date().toISOString()
            });
            
            return true;
            
        } catch (error) {
            logger.error('Error starting radar scanning:', error);
            this.io.emit('radar:error', { message: error.message });
            return false;
        }
    }
    
    stopScanning() {
        if (!this.initialized) {
            logger.warn('Radar not initialized');
            return false;
        }
        
        try {
            this.isScanning = false;
            
            // Clear scanning interval
            if (this.scanningInterval) {
                clearInterval(this.scanningInterval);
                this.scanningInterval = null;
            }
            
            logger.info('Stopped radar scanning');
            
            this.io.emit('radar:scanStopped', {
                totalScans: this.stats.totalScans,
                detections: this.stats.detectionsCount,
                timestamp: new Date().toISOString()
            });
            
            return true;
            
        } catch (error) {
            logger.error('Error stopping radar scanning:', error);
            this.io.emit('radar:error', { message: error.message });
            return false;
        }
    }
    
    async sendRadarCommand(command, args = null) {
        // Helper method to send commands to radar through Pico Master
        try {
            const fullCmd = args ? `${command}:${args}` : command;
            const response = await this.picoMaster.sendCommand('RADAR', fullCmd);
            return response;
        } catch (error) {
            logger.error(`Error sending radar command ${command}:`, error);
            throw error;
        }
    }
    
    updateConfiguration(newConfig) {
        try {
            // Update configuration
            Object.assign(this.config, newConfig);
            
            logger.info('Updated radar configuration:', newConfig);
            
            this.io.emit('radar:configUpdated', {
                config: this.config,
                timestamp: new Date().toISOString()
            });
            
            return true;
            
        } catch (error) {
            logger.error('Error updating radar configuration:', error);
            this.io.emit('radar:error', { message: error.message });
            return false;
        }
    }
    
    getStatus() {
        return {
            initialized: this.initialized,
            isScanning: this.isScanning,
            config: this.config,
            stats: this.stats,
            dataPoints: this.radarData.length,
            connected: this.serialPort ? this.serialPort.isOpen : false
        };
    }
    
    isInitialized() {
        return this.initialized;
    }
    
    getRecentData(count = 100) {
        return this.radarData.slice(-count);
    }
    
    clearData() {
        this.radarData = [];
        this.stats = {
            totalScans: 0,
            detectionsCount: 0,
            lastDetection: null,
            averageSignalStrength: 0,
            maxDistance: 0,
            minDistance: Infinity
        };
        
        this.io.emit('radar:dataCleared');
        logger.info('Radar data cleared');
    }
    
    async stop() {
        logger.info('Stopping radar controller...');
        
        this.stopScanning();
        
        this.initialized = false;
        logger.info('Radar controller stopped');
    }
}

module.exports = RadarController;