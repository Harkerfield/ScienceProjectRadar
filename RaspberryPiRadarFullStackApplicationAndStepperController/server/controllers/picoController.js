const { SerialPort } = require('serialport');
const { ReadlineParser } = require('@serialport/parser-readline');
const logger = require('../utils/logger');

class PicoController {
    constructor(io) {
        this.io = io;
        this.serialPort = null;
        this.parser = null;
        this.isConnected = false;
        this.initialized = false;
        
        // Configuration
        this.config = {
            port: process.env.PICO_UART_PORT || '/dev/ttyAMA0',
            baudRate: parseInt(process.env.PICO_UART_BAUD_RATE) || 115200,
            dataTimeout: parseInt(process.env.PICO_DATA_TIMEOUT) || 5000,
            reconnectInterval: 5000,
            maxReconnectAttempts: 10
        };
        
        // Data storage
        this.picoData = {
            radarReadings: [],
            servoStatus: null,
            systemInfo: null,
            lastDataTime: null,
            connectionStatus: 'disconnected'
        };
        
        // Statistics
        this.stats = {
            messagesReceived: 0,
            messagesSent: 0,
            lastMessageTime: null,
            reconnectAttempts: 0,
            dataErrors: 0
        };
        
        logger.info('Pico controller created');
    }
    
    async initialize() {
        try {
            logger.info('Initializing Pico UART communication...');
            
            await this.connectToPico();
            
            this.initialized = true;
            logger.info('Pico controller initialized successfully');
            
            this.io.emit('pico:initialized', {
                config: this.config,
                status: this.getStatus()
            });
            
        } catch (error) {
            logger.error('Error initializing Pico controller:', error);
            throw error;
        }
    }
    
    async connectToPico() {
        return new Promise((resolve, reject) => {
            try {
                // Initialize serial port
                this.serialPort = new SerialPort({
                    path: this.config.port,
                    baudRate: this.config.baudRate,
                    autoOpen: false
                });
                
                // Set up data parser
                this.parser = this.serialPort.pipe(new ReadlineParser({ delimiter: '\n' }));
                
                // Set up event handlers
                this.setupEventHandlers();
                
                // Open connection
                this.serialPort.open((error) => {
                    if (error) {
                        logger.error('Failed to open Pico serial port:', error);
                        reject(error);
                    } else {
                        logger.info(`Connected to Pico on ${this.config.port}`);
                        this.isConnected = true;
                        this.picoData.connectionStatus = 'connected';
                        this.stats.reconnectAttempts = 0;
                        
                        // Send initial ping
                        this.sendPing();
                        
                        resolve();
                    }
                });
                
            } catch (error) {
                logger.error('Error creating Pico connection:', error);
                reject(error);
            }
        });
    }
    
    setupEventHandlers() {
        // Serial port events
        this.serialPort.on('error', (error) => {
            logger.error('Pico serial port error:', error);
            this.isConnected = false;
            this.picoData.connectionStatus = 'error';
            this.io.emit('pico:error', { message: error.message });
            this.scheduleReconnect();
        });
        
        this.serialPort.on('close', () => {
            logger.warn('Pico serial port closed');
            this.isConnected = false;
            this.picoData.connectionStatus = 'disconnected';
            this.io.emit('pico:disconnected');
            this.scheduleReconnect();
        });
        
        this.serialPort.on('open', () => {
            logger.info('Pico serial port opened');
            this.isConnected = true;
            this.picoData.connectionStatus = 'connected';
            this.io.emit('pico:connected');
        });
        
        // Data events
        this.parser.on('data', (data) => {
            this.processIncomingData(data);
        });
    }
    
    processIncomingData(rawData) {
        try {
            const data = JSON.parse(rawData.trim());
            const messageType = data.type;
            const messageData = data.data;
            const timestamp = new Date().toISOString();
            
            this.stats.messagesReceived++;
            this.stats.lastMessageTime = timestamp;
            this.picoData.lastDataTime = timestamp;
            
            // Process different message types
            switch (messageType) {
                case 'radar_data':
                    this.handleRadarData(messageData, timestamp);
                    break;
                    \n                case 'servo_status':\n                    this.handleServoStatus(messageData, timestamp);\n                    break;\n                    \n                case 'detection':\n                    this.handleDetection(messageData, timestamp);\n                    break;\n                    \n                case 'system_info':\n                    this.handleSystemInfo(messageData, timestamp);\n                    break;\n                    \n                case 'status':\n                    this.handleStatusUpdate(messageData, timestamp);\n                    break;\n                    \n                case 'ack':\n                    this.handleAcknowledgment(messageData);\n                    break;\n                    \n                case 'error':\n                    this.handlePicoError(messageData);\n                    break;\n                    \n                default:\n                    logger.warn(`Unknown message type from Pico: ${messageType}`);\n            }\n            \n        } catch (error) {\n            logger.error('Error processing Pico data:', error);\n            this.stats.dataErrors++;\n        }\n    }\n    \n    handleRadarData(data, timestamp) {\n        const processedData = {\n            ...data,\n            timestamp,\n            source: 'pico'\n        };\n        \n        // Store radar data (limit to last 1000 readings)\n        this.picoData.radarReadings.push(processedData);\n        if (this.picoData.radarReadings.length > 1000) {\n            this.picoData.radarReadings = this.picoData.radarReadings.slice(-1000);\n        }\n        \n        // Emit to connected clients\n        this.io.emit('pico:radarData', processedData);\n        \n        logger.debug(`Received radar data: ${data.detection_count} detections`);\n    }\n    \n    handleServoStatus(data, timestamp) {\n        this.picoData.servoStatus = {\n            ...data,\n            timestamp,\n            source: 'pico'\n        };\n        \n        this.io.emit('pico:servoStatus', this.picoData.servoStatus);\n        \n        logger.debug(`Servo status: position=${data.position}, active=${data.is_active}`);\n    }\n    \n    handleDetection(data, timestamp) {\n        const detectionEvent = {\n            ...data,\n            timestamp,\n            source: 'pico',\n            id: `pico_det_${Date.now()}`\n        };\n        \n        this.io.emit('pico:detection', detectionEvent);\n        \n        logger.info(`Motion detection: ${data.detection_count} sensors triggered`);\n    }\n    \n    handleSystemInfo(data, timestamp) {\n        this.picoData.systemInfo = {\n            ...data,\n            timestamp,\n            source: 'pico'\n        };\n        \n        this.io.emit('pico:systemInfo', this.picoData.systemInfo);\n        \n        logger.info(`Pico system info updated: radar=${data.radar_type}`);\n    }\n    \n    handleStatusUpdate(data, timestamp) {\n        const statusUpdate = {\n            ...data,\n            timestamp,\n            connectionStatus: this.picoData.connectionStatus\n        };\n        \n        this.io.emit('pico:statusUpdate', statusUpdate);\n    }\n    \n    handleAcknowledgment(data) {\n        logger.debug(`Pico ACK: ${data.command} - ${data.success ? 'success' : 'failed'}`);\n        this.io.emit('pico:commandAck', data);\n    }\n    \n    handlePicoError(data) {\n        logger.error(`Pico error: ${data.error}`);\n        this.io.emit('pico:picoError', data);\n    }\n    \n    // Command sending methods\n    sendCommand(command, params = {}) {\n        if (!this.isConnected) {\n            throw new Error('Not connected to Pico');\n        }\n        \n        const message = {\n            type: 'command',\n            timestamp: Date.now(),\n            data: {\n                command,\n                params\n            }\n        };\n        \n        const messageString = JSON.stringify(message) + '\n';\n        \n        this.serialPort.write(messageString, (error) => {\n            if (error) {\n                logger.error('Error sending command to Pico:', error);\n                throw error;\n            } else {\n                this.stats.messagesSent++;\n                logger.debug(`Sent command to Pico: ${command}`);\n            }\n        });\n    }\n    \n    sendPing() {\n        try {\n            this.sendCommand('ping', { timestamp: Date.now() });\n        } catch (error) {\n            logger.warn('Failed to send ping to Pico:', error);\n        }\n    }\n    \n    requestStatus() {\n        try {\n            this.sendCommand('get_status');\n        } catch (error) {\n            logger.error('Failed to request status from Pico:', error);\n            throw error;\n        }\n    }\n    \n    controlServo(action) {\n        try {\n            this.sendCommand('servo_control', { action });\n        } catch (error) {\n            logger.error('Failed to send servo command to Pico:', error);\n            throw error;\n        }\n    }\n    \n    configureRadar(config) {\n        try {\n            this.sendCommand('radar_config', config);\n        } catch (error) {\n            logger.error('Failed to configure Pico radar:', error);\n            throw error;\n        }\n    }\n    \n    scheduleReconnect() {\n        if (this.stats.reconnectAttempts >= this.config.maxReconnectAttempts) {\n            logger.error('Max reconnection attempts reached for Pico');\n            return;\n        }\n        \n        this.stats.reconnectAttempts++;\n        \n        setTimeout(() => {\n            logger.info(`Attempting to reconnect to Pico (attempt ${this.stats.reconnectAttempts})`);\n            this.connectToPico().catch(() => {\n                // Will retry again after another interval\n            });\n        }, this.config.reconnectInterval);\n    }\n    \n    getRecentRadarData(count = 100) {\n        return this.picoData.radarReadings.slice(-count);\n    }\n    \n    getServoStatus() {\n        return this.picoData.servoStatus;\n    }\n    \n    getSystemInfo() {\n        return this.picoData.systemInfo;\n    }\n    \n    getStatus() {\n        return {\n            initialized: this.initialized,\n            connected: this.isConnected,\n            connectionStatus: this.picoData.connectionStatus,\n            config: this.config,\n            stats: this.stats,\n            dataPoints: this.picoData.radarReadings.length,\n            lastDataTime: this.picoData.lastDataTime,\n            systemInfo: this.picoData.systemInfo\n        };\n    }\n    \n    isInitialized() {\n        return this.initialized;\n    }\n    \n    async stop() {\n        logger.info('Stopping Pico controller...');\n        \n        if (this.serialPort && this.serialPort.isOpen) {\n            try {\n                // Send shutdown notification\n                this.sendCommand('system_shutdown');\n                \n                // Wait a moment for message to send\n                await new Promise(resolve => setTimeout(resolve, 100));\n                \n                await new Promise((resolve) => {\n                    this.serialPort.close(resolve);\n                });\n            } catch (error) {\n                logger.error('Error closing Pico serial port:', error);\n            }\n        }\n        \n        this.initialized = false;\n        this.isConnected = false;\n        \n        logger.info('Pico controller stopped');\n    }\n}\n\nmodule.exports = PicoController;