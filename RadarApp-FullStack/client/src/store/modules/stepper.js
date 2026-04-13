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
  SET_status(state, status) {
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
  async fetchStatus({ commit, dispatch }) {
    try {
      const response = await apiService.get('/device/stepper/status')
      if (response.data.success) {
        const data = response.data.data || response.data.response
        commit('SET_status', {
          position: data.position || 0,
          enabled: data.enabled || false,
          calibrated: data.calibrated || false,
          atHome: data.at_home || false,
          motorState: data.enabled ? 'idle' : 'error'
        })
        // Update radar sweep angle with real-time stepper position
        dispatch('radar/updateSweepAngle', data.position || 0, { root: true })
      }
      return response.data
    } catch (error) {
      console.error('Failed to fetch stepper status:', error)
      commit('SET_status', { motorState: 'error' })
      throw error
    }
  },

  async getPosition({ dispatch }) {
    // Delegate to fetchStatus to avoid duplication
    return dispatch('fetchStatus')
  },

  async moveToAngle({ commit, dispatch }, { angle, speed } = {}) {
    try {
      // Set speed if provided
      if (speed) {
        // Convert RPM-like value to microseconds (rough conversion)
        const speedUs = Math.max(500, Math.min(10000, Math.round((100 - speed) * 95 + 500)))
        await apiService.post('/device/stepper/speed', { args: { speed_us: speedUs } })
      }

      // Move to angle
      commit('SET_status', { motorState: 'moving' })
      const response = await apiService.post('/device/stepper/move', { args: { degrees: angle } })
      const data = response.data.data || response.data.response

      commit('SET_status', {
        position: data.position || angle,
        targetPosition: angle,
        motorState: 'idle'
      })

      // Update radar sweep angle in real-time
      dispatch('radar/updateSweepAngle', data.position || angle, { root: true })

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
      commit('SET_status', { motorState: 'error' })
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
        await apiService.post('/device/stepper/speed', { args: { speed_us: speedUs } })
      }

      // Start continuous rotation
      commit('SET_status', {
        motorState: 'moving',
        rotating: true,
        direction: stepperDirection
      })

      const response = await apiService.post('/device/stepper/spin', {
        args: { speed_us: 2000 }
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
      commit('SET_status', { motorState: 'error' })
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
      const response = await apiService.post('/device/stepper/stop')
      const data = response.data.data || response.data.response

      commit('SET_status', {
        motorState: 'idle',
        rotating: false,
        position: data.position || 0
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
      commit('SET_status', { motorState: 'error' })
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
      commit('SET_status', { motorState: 'moving' })
      const response = await apiService.post('/device/stepper/home')
      const data = response.data.data || response.data.response

      commit('SET_status', {
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
      commit('SET_status', { motorState: 'error' })
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
      // Update default speed if provided
      if (config.defaultSpeed) {
        await apiService.post('/device/stepper/speed', { args: { speed_us: config.defaultSpeed } })
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
  },

  async enable({ commit, dispatch }) {
    try {
      const response = await apiService.post('/device/stepper/enable')
      commit('SET_status', { enabled: true })

      commit('ADD_HISTORY_ENTRY', {
        action: 'enable',
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'success',
        title: 'Motor Enabled',
        message: 'Stepper motor has been enabled'
      }, { root: true })

      return response.data
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'enable',
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Enable Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async disable({ commit, dispatch }) {
    try {
      const response = await apiService.post('/device/stepper/disable')
      commit('SET_status', { enabled: false })

      commit('ADD_HISTORY_ENTRY', {
        action: 'disable',
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'info',
        title: 'Motor Disabled',
        message: 'Stepper motor has been disabled'
      }, { root: true })

      return response.data
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'disable',
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Disable Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async ping({ commit, _dispatch }) {
    try {
      const response = await apiService.get('/device/stepper/ping')
      commit('ADD_HISTORY_ENTRY', {
        action: 'ping',
        success: true
      })
      return response.data
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'ping',
        success: false,
        error: error.message
      })
      throw error
    }
  },

  async getInfo({ _commit, _dispatch }) {
    try {
      const response = await apiService.get('/device/stepper/whoami')
      return response.data
    } catch (error) {
      console.error('Failed to get stepper info:', error)
      throw error
    }
  },

  /**
   * Raise stepper to full extent (360°)
   */
  async raise({ dispatch }) {
    try {
      await dispatch('moveToAngle', { angle: 360 })
    } catch (error) {
      console.error('Failed to raise:', error)
      throw error
    }
  },

  /**
   * Lower stepper to minimum (0°)
   */
  async lower({ dispatch }) {
    try {
      await dispatch('moveToAngle', { angle: 0 })
    } catch (error) {
      console.error('Failed to lower:', error)
      throw error
    }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
