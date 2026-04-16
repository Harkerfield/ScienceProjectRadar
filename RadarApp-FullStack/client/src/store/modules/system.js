  SET_ALL_SETTINGS(state, settings) {
    // Merge all settings into state; adjust as needed for your structure
    if (settings.systemInfo) {
      state.systemInfo = { ...state.systemInfo, ...settings.systemInfo }
    }
    if (settings.uptime !== undefined) {
      state.uptime = settings.uptime
    }
    if (settings.systemStatus) {
      state.systemStatus = settings.systemStatus
    }
    // Add more fields as needed for your app
  },
  updateSettings({ commit }, settings) {
    commit('SET_ALL_SETTINGS', settings)
  },
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
  SET_SYSTEM_status(state, status) {
    state.systemStatus = status
  },

  SET_UPTIME(state, uptime) {
    state.uptime = uptime
  },

  SET_HEARTBEAT(state, timestamp) {
    state.lastHeartbeat = timestamp
  },

  ADD_error_LOG(state, error) {
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

  CLEAR_error_LOGS(state) {
    state.errorLogs = []
  },

  SET_SYSTEM_INFO(state, info) {
    state.systemInfo = { ...state.systemInfo, ...info }
  },

  SET_ONLINE_status(state, isOnline) {
    state.isOnline = isOnline
  }
}

const actions = {
  updateSystemStatus({ commit }, status) {
    commit('SET_SYSTEM_status', status)
  },

  updateUptime({ commit }, uptime) {
    commit('SET_UPTIME', uptime)
  },

  recordHeartbeat({ commit }) {
    commit('SET_HEARTBEAT', Date.now())
    commit('SET_ONLINE_status', true)
  },

  logError({ commit }, error) {
    commit('ADD_error_LOG', error)
  },

  clearErrors({ commit }) {
    commit('CLEAR_error_LOGS')
  },

  updateSystemInfo({ commit }, info) {
    commit('SET_SYSTEM_INFO', info)
  },

  setOffline({ commit }) {
    commit('SET_ONLINE_status', false)
    commit('SET_SYSTEM_status', 'offline')
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
