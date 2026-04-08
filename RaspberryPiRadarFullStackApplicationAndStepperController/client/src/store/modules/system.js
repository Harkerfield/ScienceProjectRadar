const state = {
  systemStatus: 'idle', // idle, running, error, maintenance
  uptime: 0,
  lastHeartbeat: null,
  errorLogs: [],
  systemInfo: {
    version: '1.0.0',
    platform: null,
    memory: null,
    cpu: null
  },
  isOnline: false
}

const getters = {
  systemStatus: state => state.systemStatus,
  uptime: state => state.uptime,
  lastHeartbeat: state => state.lastHeartbeat,
  errorLogs: state => state.errorLogs,
  systemInfo: state => state.systemInfo,
  isOnline: state => state.isOnline,
  hasErrors: state => state.errorLogs.length > 0
}

const mutations = {
  SET_SYSTEM_STATUS(state, status) {
    state.systemStatus = status
  },

  SET_UPTIME(state, uptime) {
    state.uptime = uptime
  },

  SET_HEARTBEAT(state, timestamp) {
    state.lastHeartbeat = timestamp
  },

  ADD_ERROR_LOG(state, error) {
    state.errorLogs.unshift({
      id: Date.now(),
      timestamp: new Date().toISOString(),
      message: error.message || error,
      type: error.type || 'error',
      source: error.source || 'system'
    })

    // Keep only last 100 errors
    if (state.errorLogs.length > 100) {
      state.errorLogs = state.errorLogs.slice(0, 100)
    }
  },

  CLEAR_ERROR_LOGS(state) {
    state.errorLogs = []
  },

  SET_SYSTEM_INFO(state, info) {
    state.systemInfo = { ...state.systemInfo, ...info }
  },

  SET_ONLINE_STATUS(state, isOnline) {
    state.isOnline = isOnline
  }
}

const actions = {
  updateSystemStatus({ commit }, status) {
    commit('SET_SYSTEM_STATUS', status)
  },

  updateUptime({ commit }, uptime) {
    commit('SET_UPTIME', uptime)
  },

  recordHeartbeat({ commit }) {
    commit('SET_HEARTBEAT', Date.now())
    commit('SET_ONLINE_STATUS', true)
  },

  logError({ commit }, error) {
    commit('ADD_ERROR_LOG', error)
  },

  clearErrors({ commit }) {
    commit('CLEAR_ERROR_LOGS')
  },

  updateSystemInfo({ commit }, info) {
    commit('SET_SYSTEM_INFO', info)
  },

  setOffline({ commit }) {
    commit('SET_ONLINE_STATUS', false)
    commit('SET_SYSTEM_STATUS', 'offline')
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
