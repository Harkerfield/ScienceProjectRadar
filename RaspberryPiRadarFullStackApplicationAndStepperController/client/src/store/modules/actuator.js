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
  SET_STATUS(state, status) {
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
      const response = await apiService.get('/actuator/status')
      const data = response.data.data || response.data
      commit('SET_STATUS', data)
      return data
    } catch (error) {
      console.error('Failed to fetch actuator status:', error)
      throw error
    }
  },

  async getPosition({ commit }) {
    try {
      const response = await apiService.get('/actuator/position')
      const data = response.data.data || response.data
      commit('SET_STATUS', {
        position: data.position,
        state: data.state,
        isOpen: data.state === 'open'
      })
      return data
    } catch (error) {
      console.error('Failed to get actuator position:', error)
      throw error
    }
  },

  async open({ commit, dispatch }) {
    try {
      const response = await apiService.put('/actuator/open')
      const data = response.data.data || response.data

      commit('SET_STATUS', {
        position: data.position,
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
      const response = await apiService.put('/actuator/close')
      const data = response.data.data || response.data

      commit('SET_STATUS', {
        position: data.position,
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
      const response = await apiService.put('/actuator/position', { position })
      const data = response.data.data || response.data

      commit('SET_STATUS', {
        position: data.position,
        state: data.state,
        isOpen: data.state === 'open'
      })

      commit('ADD_HISTORY_ENTRY', {
        action: 'setPosition',
        position,
        success: true
      })

      dispatch('notifications/addNotification', {
        type: 'success',
        title: 'Position Set',
        message: `Actuator position set to ${position}%`
      }, { root: true })
    } catch (error) {
      commit('ADD_HISTORY_ENTRY', {
        action: 'setPosition',
        position,
        success: false,
        error: error.message
      })

      dispatch('notifications/addNotification', {
        type: 'error',
        title: 'Set Position Failed',
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
