import apiService from '../../services/apiService'

const state = {
  status: {
    initialized: false,
    position: 0,
    state: 'unknown', // 'open', 'closed', 'unknown'
    isOpen: false,
    lastUpdate: null
  },
  history: [],
  maxHistoryLength: 100
}

const getters = {
  position: state => state.status.position,
  state: state => state.status.state,
  isOpen: state => state.status.isOpen,
  isClosed: state => state.status.state === 'closed',
  recentHistory: state => state.history.slice(-10)
}

const mutations = {
  SET_status(state, status) {
    state.status = { ...state.status, ...status, lastUpdate: new Date().toISOString() }
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
      const response = await apiService.get('/device/servo/status')
      const data = response.data.data || response.data.response
      commit('SET_status', {
        state: data.state || 'unknown',
        isOpen: data.state === 'open'
      })
      return data
    } catch (error) {
      console.error('Failed to fetch actuator status:', error)
      throw error
    }
  },

  async getPosition({ dispatch }) {
    // Delegate to fetchStatus to avoid duplication
    return dispatch('fetchStatus')
  },

  async open({ commit, dispatch }) {
    try {
      const response = await apiService.post('/device/servo/open')
      const _data = response.data.data || response.data.response

      commit('SET_status', {
        state: 'open',
        isOpen: true
      })

      commit('ADD_HISTORY_ENTRY', {
        action: 'open',
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'success',
        title: 'Actuator Opened',
        message: 'Actuator has been opened/extended'
      }, { root: true })
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'open',
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Open Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async close({ commit, dispatch }) {
    try {
      const response = await apiService.post('/device/servo/close')
      const _data = response.data.data || response.data.response

      commit('SET_status', {
        state: 'closed',
        isOpen: false
      })

      commit('ADD_HISTORY_ENTRY', {
        action: 'close',
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'success',
        title: 'Actuator Closed',
        message: 'Actuator has been closed/retracted'
      }, { root: true })
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'close',
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Close Failed',
        message: error.response?.data?.error || error.message
      }, { root: true })

      throw error
    }
  },

  async setPosition({ commit, dispatch }, position) {
    try {
      // Note: Direct position setting is not supported by the servo API
      // Use open or close instead
      throw new Error('Direct position setting not supported. Use open() or close()')
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'setPosition',
        position,
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Set Position Not Supported',
        message: 'Use open() or close() instead'
      }, { root: true })

      throw error
    }
  },

  clearHistory({ commit }) {
    commit('CLEAR_HISTORY')
  },

  async ping({ commit, _dispatch }) {
    try {
      const response = await apiService.get('/device/servo/ping')
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
      const response = await apiService.get('/device/servo/whoami')
      return response.data
    } catch (error) {
      console.error('Failed to get servo info:', error)
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
