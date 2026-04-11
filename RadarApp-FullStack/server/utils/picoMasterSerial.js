// Node.js utility for communicating with the master Pico via serial
// Protocol: DEVICE:COMMAND[:ARGS]\n
// Response: DEVICE:STATUS[:KEY=VALUE:KEY=VALUE]\n

const { SerialPort } = require('serialport');
const { ReadlineParser } = require('@serialport/parser-readline');
const logger = require('./logger');

class PicoMasterSerial {
  constructor(options = {}) {
    this.portPath = options.port || process.env.PICO_UART_PORT || '/dev/ttyACM0';
    this.baudRate = options.baudRate || parseInt(process.env.PICO_UART_BAUD_RATE) || 115200;
    this.timeout = options.timeout || 5000;
    this.isConnected = false;
    this.port = null;
    this.parser = null;
    this.pendingRequests = {};
    this.requestId = 0;
    this.deviceCache = {
      STEPPER: {},
      SERVO: {},
      RADAR: {}
    };
  }

  /**
   * Initialize the serial connection
   */
  async connect() {
    return new Promise((resolve, reject) => {
      try {
        this.port = new SerialPort({
          path: this.portPath,
          baudRate: this.baudRate,
          autoOpen: false
        });

        this.parser = this.port.pipe(new ReadlineParser({ delimiter: '\n' }));

        // Handle incoming data
        this.parser.on('data', (line) => {
          try {
            const data = line.trim();
            if (data) {
              this._handleResponse(data);
            }
          } catch (error) {
            logger.error('Error handling response:', error, line);
          }
        });

        // Handle connection events
        this.port.on('error', (error) => {
          logger.error('Serial port error:', error);
          this.isConnected = false;
          reject(error);
        });

        this.port.open((error) => {
          if (error) {
            logger.error('Failed to open serial port:', error);
            reject(error);
          } else {
            logger.info(`Connected to Pico on ${this.portPath} at ${this.baudRate} baud`);
            this.isConnected = true;
            resolve();
          }
        });
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Send a command to a Pico device
   * @param {string} device - Device name (STEPPER, SERVO, RADAR)
   * @param {string} command - Command to send
   * @param {string|null} args - Optional command arguments
   * @param {number|null} timeout - Optional timeout override
   * @returns {Promise<Object>} Parsed response
   */
  async sendDeviceCommand(device, command, args = null, timeout = null) {
    if (!this.isConnected) {
      throw new Error('Not connected to Pico');
    }

    // Build command
    let fullCmd = `${device}:${command}`;
    if (args !== null && args !== undefined) {
      fullCmd += `:${args}`;
    }

    const timeoutMs = timeout || this.timeout;
    const requestId = ++this.requestId;

    return new Promise((resolve, reject) => {
      // Set timeout
      const timeoutHandle = setTimeout(() => {
        delete this.pendingRequests[device];
        logger.warn(`Timeout waiting for response from ${device} (${fullCmd})`);
        reject(new Error(`Timeout: No response from ${device} after ${timeoutMs}ms`));
      }, timeoutMs);

      // Register pending request
      this.pendingRequests[device] = {
        requestId,
        resolve: (data) => {
          clearTimeout(timeoutHandle);
          resolve(data);
        },
        reject: (error) => {
          clearTimeout(timeoutHandle);
          reject(error);
        }
      };

      try {
        // Send command
        logger.debug(`Sending to Pico: ${fullCmd}`);
        this.port.write(fullCmd + '\n', (error) => {
          if (error) {
            clearTimeout(timeoutHandle);
            delete this.pendingRequests[device];
            reject(error);
          }
        });
      } catch (error) {
        clearTimeout(timeoutHandle);
        delete this.pendingRequests[device];
        reject(error);
      }
    });
  }

  /**
   * Handle response from Pico
   * @private
   */
  _handleResponse(response) {
    try {
      // Parse DEVICE:STATUS[:DATA]
      const colonIndex = response.indexOf(':');
      if (colonIndex === -1) {
        logger.warn('Invalid response format:', response);
        return;
      }

      const device = response.substring(0, colonIndex);
      const statusData = response.substring(colonIndex + 1);

      // Check if we're waiting for this device
      if (!this.pendingRequests[device]) {
        logger.debug(`Received unsolicited response from ${device}: ${statusData}`);
        return;
      }

      // Parse the response
      const parsed = this._parseResponse(device, statusData);

      // Resolve pending request
      const pending = this.pendingRequests[device];
      delete this.pendingRequests[device];
      pending.resolve(parsed);
    } catch (error) {
      logger.error('Error handling response:', error);
    }
  }

  /**
   * Parse device response in format: STATUS[:KEY=VALUE:KEY=VALUE]
   * @private
   */
  _parseResponse(device, statusData) {
    const parts = statusData.split(':');
    const status = parts[0];

    // Check for error
    if (status === 'ERROR') {
      const errorMsg = parts[1] || 'Unknown error';
      return {
        success: false,
        status: 'ERROR',
        error: errorMsg,
        raw: statusData
      };
    }

    if (status !== 'OK') {
      return {
        success: false,
        status: status,
        error: 'Invalid status',
        raw: statusData
      };
    }

    // Parse KEY=VALUE pairs
    const data = {};
    for (let i = 1; i < parts.length; i++) {
      const pair = parts[i];
      const eqIndex = pair.indexOf('=');
      if (eqIndex > -1) {
        const key = pair.substring(0, eqIndex);
        const value = pair.substring(eqIndex + 1);
        data[key] = this._parseValue(value);
      }
    }

    return {
      success: true,
      status: 'OK',
      data: data,
      raw: statusData,
      device: device,
      timestamp: Date.now()
    };
  }

  /**
   * Parse value, attempting to convert to appropriate type
   * @private
   */
  _parseValue(value) {
    // Try to parse as number
    if (!isNaN(value) && value !== '') {
      const num = Number(value);
      return num;
    }

    // Try to parse as boolean
    if (value === 'true' || value === '1') return true;
    if (value === 'false' || value === '0') return false;

    // Return as string
    return value;
  }

  /**
   * Disconnect from Pico
   */
  disconnect() {
    return new Promise((resolve) => {
      if (this.port && this.isConnected) {
        this.port.close(() => {
          this.isConnected = false;
          logger.info('Disconnected from Pico');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }

  /**
   * Get device cache
   */
  getCachedData(device) {
    return this.deviceCache[device] || {};
  }

  /**
   * Update device cache
   */
  updateCache(device, data) {
    this.deviceCache[device] = { ...this.deviceCache[device], ...data };
  }
}

// Create and export singleton
let instance = null;

function getInstance(options = {}) {
  if (!instance) {
    instance = new PicoMasterSerial(options);
  }
  return instance;
}

module.exports = {
  getInstance,
  PicoMasterSerial
};
