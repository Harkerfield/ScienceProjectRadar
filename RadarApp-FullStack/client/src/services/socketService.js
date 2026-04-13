import { io } from 'socket.io-client'

// Determine Socket.io URL intelligently
function getSocketUrl() {
  // Check if explicitly set in environment
  if (process.env.VUE_APP_SOCKET_URL) {
    console.log('Using VUE_APP_SOCKET_URL:', process.env.VUE_APP_SOCKET_URL)
    return process.env.VUE_APP_SOCKET_URL
  }

  // Auto-detect based on current location
  const hostname = window.location.hostname
  const port = window.location.port || 3000
  const url = `http://${hostname}:${port}`

  console.log('Socket.io auto-detected URL:', {
    hostname,
    port,
    fullUrl: url,
    windowLocation: window.location.href
  })

  return url
}

class SocketService {
  constructor() {
    this.socket = null
    this.store = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectInterval = null
  }

  init(store) {
    this.store = store
  }

  async connect(url = null) {
    const socketUrl = url || getSocketUrl()

    try {
      this.socket = io(socketUrl, {
        timeout: 10000,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: 2000,
        autoConnect: true
      })

      this.setupEventHandlers()
      this.setupRadarHandlers()
      this.setupPicoHandlers()

      // Wait for connection
      return new Promise((resolve, reject) => {
        this.socket.on('connect', () => {
          console.log('Socket connected:', this.socket.id)
          this.reconnectAttempts = 0

          if (this.store) {
            this.store.dispatch('connection/setConnected', true)
          }

          resolve()
        })

        this.socket.on('connect_error', (error) => {
          console.error('Socket connection error:', error)

          if (this.store) {
            this.store.dispatch('notifications/addNotification', {
              type: 'error',
              title: 'Connection Error',
              message: 'Failed to connect to server'
            })
          }

          reject(error)
        })

        // Timeout fallback
        setTimeout(() => {
          if (!this.socket.connected) {
            reject(new Error('Connection timeout'))
          }
        }, 10000)
      })
    } catch (error) {
      console.error('Failed to create socket connection:', error)
      throw error
    }
  }

  setupEventHandlers() {
    if (!this.socket) return

    this.socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason)

      if (this.store) {
        this.store.dispatch('connection/setConnected', false)
      }
    })

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('Socket reconnected after', attemptNumber, 'attempts')
      this.reconnectAttempts = 0

      if (this.store) {
        this.store.dispatch('connection/setConnected', true)
        this.store.dispatch('notifications/addNotification', {
          type: 'success',
          title: 'Reconnected',
          message: 'Connection to server restored'
        })
      }
    })

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log('Socket reconnection attempt:', attemptNumber)
      this.reconnectAttempts = attemptNumber

      if (this.store) {
        this.store.dispatch('notifications/addNotification', {
          type: 'info',
          title: 'Reconnecting...',
          message: `Attempt ${attemptNumber} of ${this.maxReconnectAttempts}`
        })
      }
    })

    this.socket.on('reconnect_error', (error) => {
      console.error('Socket reconnection error:', error)
    })

    this.socket.on('reconnect_failed', () => {
      console.error('Socket reconnection failed after maximum attempts')

      if (this.store) {
        this.store.dispatch('notifications/addNotification', {
          type: 'error',
          title: 'Connection Failed',
          message: 'Could not reconnect to server after multiple attempts'
        })
      }
    })

    // System heartbeat tracking
    this.socket.on('system:status', () => {
      if (this.store) {
        this.store.dispatch('system/recordHeartbeat')
      }
    })

    // Stepper motor events
    this.socket.on('stepperStatus', (data) => {
      if (this.store) {
        this.store.dispatch('stepper/updateStatus', data)
      }
    })

    this.socket.on('stepperPosition', (data) => {
      if (this.store) {
        this.store.dispatch('stepper/updateStatus', data)
      }
    })

    this.socket.on('stepperError', (data) => {
      if (this.store) {
        this.store.dispatch('stepper/updateStatus', data)
        this.store.dispatch('notifications/addNotification', {
          type: 'error',
          title: 'Stepper Error',
          message: data.message || 'Stepper motor error occurred'
        })
      }
    })
  }

  setupRadarHandlers() {
    if (!this.socket || !this.store) return

    // Local radar events
    this.socket.on('radarData', (data) => {
      this.store.dispatch('radar/processRadarData', data)
    })

    this.socket.on('radarStatus', (data) => {
      if (data.isScanning !== undefined) {
        this.store.commit('radar/SET_SCANNING_STATE', data.isScanning)
      }
    })

    this.socket.on('radarCalibration', (data) => {
      this.store.dispatch('radar/setCalibrationData', data)
    })

    this.socket.on('radarError', (data) => {
      this.store.commit('radar/ADD_error', data)
      this.store.dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Radar Error',
        message: data.message || 'Radar system error'
      })
    })
  }

  setupPicoHandlers() {
    if (!this.socket || !this.store) return

    // Pico connection status
    this.socket.on('picoConnected', (data) => {
      this.store.dispatch('pico/handlePicoConnection', data.connected)
    })

    // Pico radar data
    this.socket.on('picoRadarData', (data) => {
      this.store.commit('pico/ADD_PICO_RADAR_DATA', data)
    })

    // Pico servo status
    this.socket.on('picoServoStatus', (data) => {
      this.store.commit('pico/UPDATE_servo_status', data)
    })

    // Pico general status
    this.socket.on('picoStatus', (data) => {
      this.store.commit('pico/UPDATE_PICO_status', data)
    })

    // Pico command responses
    this.socket.on('picoCommandResponse', (data) => {
      this.store.dispatch('pico/processPicoMessage', {
        type: 'command_response',
        data
      })
    })

    // Pico errors
    this.socket.on('picoError', (data) => {
      this.store.dispatch('pico/processPicoMessage', {
        type: 'error',
        data
      })
    })
  }

  emit(event, data) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data)
      console.log(`Socket emit: ${event}`, data)
    } else {
      console.warn(`Cannot emit ${event}: socket not connected`)
    }
  }

  // Convenience methods for radar operations
  startRadar(config = {}) {
    this.emit('startRadar', config)
  }

  stopRadar() {
    this.emit('stopRadar')
  }

  configureRadar(config) {
    this.emit('configureRadar', config)
  }

  calibrateRadar() {
    this.emit('calibrateRadar')
  }

  // Convenience methods for Pico operations
  sendPicoCommand(command, params = null) {
    this.emit('picoCommand', { command, params })
  }

  controlServo(action, params = {}) {
    this.emit('picoCommand', { command: `servo_${action}`, params })
  }

  requestPicoStatus() {
    this.emit('picoCommand', { command: 'get_status' })
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback)
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback)
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  isConnected() {
    return this.socket && this.socket.connected
  }

  getConnectionStatus() {
    if (!this.socket) return 'disconnected'
    if (this.socket.connected) return 'connected'
    if (this.socket.connecting) return 'connecting'
    return 'disconnected'
  }
}

// Export singleton instance
export default new SocketService()
