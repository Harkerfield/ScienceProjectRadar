import socketService from '../../services/socketService'

const state = {
  connectionStatus: 'disconnected', // 'connected', 'connecting', 'disconnected', 'error'
  websocketStatus: 'disconnected', // WebSocket (server) status
  serialConnected: false, // Serial bridge (Python) connection status
  picoConnected: false, // Pico master device status
  lastConnected: null,
  reconnectAttempts: 0,
  maxReconnectAttempts: 5
}

const getters = {
  isConnected: state => state.connectionStatus === 'connected',
  isConnecting: state => state.connectionStatus === 'connecting',
  allConnected: state => state.websocketStatus === 'connected' && state.serialConnected && state.picoConnected,
  connectionStatusText: state => {
    switch (state.connectionStatus) {
    case 'connected': return 'Connected'
    case 'connecting': return 'Connecting...'
    case 'disconnected': return 'Disconnected'
    case 'error': return 'Connection Error'
    default: return 'Unknown'
    }
  },
  websocketStatusText: state => {
    switch (state.websocketStatus) {
    case 'connected': return 'Connected'
    case 'connecting': return 'Connecting...'
    case 'disconnected': return 'Disconnected'
    case 'error': return 'Connection Error'
    default: return 'Unknown'
    }
  },
  serialStatusText: state => state.serialConnected ? 'Connected' : 'Disconnected',
  picoStatusText: state => state.picoConnected ? 'Connected' : 'Disconnected'
}

const mutations = {
  SET_CONNECTION_status(state, status) {
    state.connectionStatus = status
    state.websocketStatus = status
    if (status === 'connected') {
      state.lastConnected = new Date().toISOString()
      state.reconnectAttempts = 0
    }
  },

  SET_WEBSOCKET_status(state, status) {
    state.websocketStatus = status
  },

  SET_SERIAL_CONNECTED(state, connected) {
    state.serialConnected = connected
  },

  SET_PICO_CONNECTED(state, connected) {
    state.picoConnected = connected
  },

  INCREMENT_RECONNECT_ATTEMPTS(state) {
    state.reconnectAttempts++
  },

  RESET_RECONNECT_ATTEMPTS(state) {
    state.reconnectAttempts = 0
  }
}

const actions = {
  async initializeConnection({ commit, dispatch }) {
    commit('SET_CONNECTION_status', 'connecting')

    try {
      await socketService.connect()
      commit('SET_CONNECTION_status', 'connected')

      // Set up socket event listeners
      dispatch('setupSocketListeners')
    } catch (error) {
      console.error('Failed to connect:', error)
      commit('SET_CONNECTION_status', 'error')

      // Attempt reconnection
      dispatch('attemptReconnection')
    }
  },

  setupSocketListeners({ commit, dispatch, rootState: _rootState }) {
    socketService.on('connect', () => {
      commit('SET_CONNECTION_status', 'connected')
      dispatch('notifications/addNotification', {
        type: 'success',
        title: 'Connected',
        message: 'Successfully connected to server'
      }, { root: true })
    })

    socketService.on('disconnect', () => {
      commit('SET_CONNECTION_status', 'disconnected')
      dispatch('notifications/addNotification', {
        type: 'warning',
        title: 'Disconnected',
        message: 'Lost connection to server'
      }, { root: true })
    })

    socketService.on('connect_error', (error) => {
      console.error('Connection error:', error)
      commit('SET_CONNECTION_status', 'error')
      dispatch('attemptReconnection')
    })

    // System status events
    socketService.on('system:status', (data) => {
      dispatch('system/updateStatus', data, { root: true })
    })

    // Stepper events
    socketService.on('stepper:started', (data) => {
      dispatch('stepper/handleStarted', data, { root: true })
    })

    socketService.on('stepper:stopped', (data) => {
      dispatch('stepper/handleStopped', data, { root: true })
    })

    socketService.on('stepper:speedChanged', (data) => {
      dispatch('stepper/handleSpeedChanged', data, { root: true })
    })

    socketService.on('stepper:directionChanged', (data) => {
      dispatch('stepper/handleDirectionChanged', data, { root: true })
    })

    socketService.on('stepper:progress', (data) => {
      dispatch('stepper/handleProgress', data, { root: true })
    })

    // Radar events
    socketService.on('radar:data', (data) => {
      dispatch('radar/addDataPoint', data, { root: true })
    })

    socketService.on('radar:detection', (data) => {
      dispatch('radar/handleDetection', data, { root: true })
    })

    socketService.on('radar:scanStarted', (data) => {
      dispatch('radar/handleScanStarted', data, { root: true })
    })

    socketService.on('radar:scanStopped', (data) => {
      dispatch('radar/handleScanStopped', data, { root: true })
    })

    // System status to track Pico and Serial connection
    socketService.on('system:status', (data) => {
      if (data.serial) {
        commit('SET_SERIAL_CONNECTED', data.serial.connected || false)
      }
      if (data.pico) {
        const picoConnected = data.pico.status !== 'unavailable' && data.pico.initialized
        commit('SET_PICO_CONNECTED', picoConnected)
      }
    })
  },

  setConnected({ commit }, isConnected) {
    commit('SET_CONNECTION_status', isConnected ? 'connected' : 'disconnected')
  },

  async attemptReconnection({ state, commit, dispatch }) {
    if (state.reconnectAttempts >= state.maxReconnectAttempts) {
      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Connection Failed',
        message: 'Maximum reconnection attempts reached'
      }, { root: true })
      return
    }

    commit('INCREMENT_RECONNECT_ATTEMPTS')

    setTimeout(() => {
      dispatch('initializeConnection')
    }, 2000 * state.reconnectAttempts) // Exponential backoff
  },

  disconnect({ commit }) {
    socketService.disconnect()
    commit('SET_CONNECTION_status', 'disconnected')
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
