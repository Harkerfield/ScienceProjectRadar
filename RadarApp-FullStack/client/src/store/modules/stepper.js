import apiService from '../../services/apiService'

const state = {
  status: {
    initialized: false,
    position: 0,
    targetPosition: 0,
    motorState: 'idle', // idle, moving, error
    currentSpeed: 2000, // in microseconds
    enabled: false,
    calibrated: false,
    direction: 'CW',
    rotating: false,
    atHome: false,
    lastUpdate: null
  },
  config: {
    minSpeed: 500,
    maxSpeed: 10000,
    defaultSpeed: 2000
  },
  history: [],
  maxHistoryLength: 100
}

const getters = {
  currentPosition: state => state.status.position,
  targetPosition: state => state.status.targetPosition,
  motorState: state => state.status.motorState,
  currentSpeed: state => state.status.currentSpeed,
  isMoving: state => state.status.motorState === 'moving',
  isEnabled: state => state.status.enabled,
  isCalibrated: state => state.status.calibrated,
  directionText: state => state.status.direction === 'CW' ? 'Clockwise' : 'Counter-clockwise',
  recentHistory: state => state.history.slice(-10)
}

const mutations = {
  SET_STATUS(state, status) {
    state.status = { ...state.status, ...status, lastUpdate: new Date().toISOString() }
  },

  SET_CONFIG(state, config) {
    state.config = { ...state.config, ...config }
  },

  ADD_HISTORY_ENTRY(state, entry) {
    state.history.push({
      ...entry,
      timestamp: new Date().toISOString()
    })

    // Limit history length
    if (state.history.length > state.maxHistoryLength) {
      state.history = state.history.slice(-state.maxHistoryLength)
    }
  },

  CLEAR_HISTORY(state) {
    state.history = []
  }
}

const actions = {
  async fetchStatus({ commit }) {
    try {
      const response = await apiService.get('/stepper/status')
      if (response.data.success) {
        commit('SET_STATUS', response.data.data)
      } else {
        commit('SET_STATUS', response.data)
      }
      return response.data
    } catch (error) {
      console.error('Failed to fetch stepper status:', error)
      commit('SET_STATUS', { motorState: 'error' })
      throw error
    }
  },

  async getPosition({ commit }) {
    try {
      const response = await apiService.get('/stepper/position')
      const data = response.data.data || response.data
      commit('SET_STATUS', {
        position: data.position || data.degrees,
        calibrated: data.calibrated
      })
      return data
    } catch (error) {
      console.error('Failed to get position:', error)
      throw error
    }
  },

  async moveToAngle({ commit, dispatch }, { angle, speed } = {}) {
    try {
      // Set speed if provided
      if (speed) {
        // Convert RPM-like value to microseconds (rough conversion)
        const speedUs = Math.max(500, Math.min(10000, Math.round((100 - speed) * 95 + 500)))
        await apiService.put('/stepper/speed', { speed: speedUs })
      }

      // Move to angle
      commit('SET_STATUS', { motorState: 'moving' })
      const response = await apiService.put('/stepper/move', { angle })
      const data = response.data.data || response.data

      commit('SET_STATUS', {
        position: data.position || angle,
        targetPosition: angle,
        motorState: 'idle'
      })

      commit('ADD_HISTORY_ENTRY', {
        action: 'moveToAngle',
        angle,
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'success',
        title: 'Motor Moved',
        message: `Motor moved to ${angle}°`
      }, { root: true })
    } catch (error) {
      commit('SET_STATUS', { motorState: 'error' })
      commit('ADD_HISTORY_ENTRY', {
        action: 'moveToAngle',
        angle,
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Move Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async rotateDirection({ commit, dispatch }, { direction, speed } = {}) {
    try {
      // Convert direction to Pico format
      const stepperDirection = direction === 'cw' ? 'CW' : 'CCW'

      // Set speed if provided
      if (speed) {
        const speedUs = Math.max(500, Math.min(10000, Math.round((100 - speed) * 95 + 500)))
        await apiService.put('/stepper/speed', { speed: speedUs })
      }

      // Start continuous rotation
      commit('SET_STATUS', {
        motorState: 'moving',
        rotating: true,
        direction: stepperDirection
      })

      const response = await apiService.put('/stepper/continuous', {
        rotating: true,
        direction: stepperDirection
      })

      commit('ADD_HISTORY_ENTRY', {
        action: 'rotateDirection',
        direction: stepperDirection,
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'info',
        title: 'Rotation Started',
        message: `Motor rotating ${stepperDirection}`
      }, { root: true })

      return response.data
    } catch (error) {
      commit('SET_STATUS', { motorState: 'error' })
      commit('ADD_HISTORY_ENTRY', {
        action: 'rotateDirection',
        direction,
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Rotation Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async stopRotation({ commit, dispatch }) {
    try {
      const response = await apiService.put('/stepper/continuous', { rotating: false })
      const data = response.data.data || response.data

      commit('SET_STATUS', {
        motorState: 'idle',
        rotating: false,
        position: data.position || state.status.position
      })

      commit('ADD_HISTORY_ENTRY', {
        action: 'stop',
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'info',
        title: 'Motor Stopped',
        message: 'Motor has been stopped'
      }, { root: true })
    } catch (error) {
      commit('SET_STATUS', { motorState: 'error' })
      commit('ADD_HISTORY_ENTRY', {
        action: 'stop',
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Stop Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async homePosition({ commit, dispatch }) {
    try {
      commit('SET_STATUS', { motorState: 'moving' })
      const response = await apiService.put('/stepper/home')
      const data = response.data.data || response.data

      commit('SET_STATUS', {
        position: 0,
        calibrated: true,
        atHome: true,
        motorState: 'idle'
      })

      commit('ADD_HISTORY_ENTRY', {
        action: 'home',
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'success',
        title: 'Home Calibrated',
        message: 'Motor home position calibrated'
      }, { root: true })

      return data
    } catch (error) {
      commit('SET_STATUS', { motorState: 'error' })
      commit('ADD_HISTORY_ENTRY', {
        action: 'home',
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Home Calibration Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async updateConfiguration({ commit, dispatch }, config) {
    try {
      // Note: These are primarily server-side configuration settings
      // The Pico firmware doesn't directly support changing min/max speed limits
      if (config.minSpeed) {
        await apiService.put('/stepper/min-speed', { minSpeed: config.minSpeed })
      }
      if (config.maxSpeed) {
        await apiService.put('/stepper/max-speed', { maxSpeed: config.maxSpeed })
      }

      commit('SET_CONFIG', config)
      commit('ADD_HISTORY_ENTRY', {
        action: 'updateConfiguration',
        config,
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'info',
        title: 'Configuration Updated',
        message: 'Motor configuration has been updated'
      }, { root: true })
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'updateConfiguration',
        config,
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Configuration Update Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  clearHistory({ commit }) {
    commit('CLEAR_HISTORY')
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
