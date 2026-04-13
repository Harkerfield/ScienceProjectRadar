export default {
  namespaced: true,

  state: {
    notifications: [],
    maxNotifications: 10,
    defaultTimeout: 5000
  },

  getters: {
    notifications: (state) => {
      return state.notifications.filter(notification => !notification.dismissed)
    },

    activeNotifications: (state) => {
      return state.notifications.filter(notification => !notification.dismissed)
    },

    recentNotifications: (state) => {
      return state.notifications.slice(-20) // Keep last 20 for history
    },

    emergencyNotifications: (state) => {
      return state.notifications.filter(n => n.type === 'emergency' && !n.dismissed)
    },

    errorNotifications: (state) => {
      return state.notifications.filter(n => n.type === 'error' && !n.dismissed)
    },

    hasUnreadErrors: (state, getters) => {
      return getters.errorNotifications.length > 0
    },

    hasEmergency: (state, getters) => {
      return getters.emergencyNotifications.length > 0
    }
  },

  mutations: {
    ADD_NOTIFICATION(state, notification) {
      // ID and timeout already set by the action
      const newNotification = {
        timestamp: new Date().toISOString(),
        dismissed: false,
        read: false,
        ...notification
      }

      state.notifications.push(newNotification)

      // Keep only max notifications
      if (state.notifications.length > state.maxNotifications * 2) {
        state.notifications = state.notifications.slice(-state.maxNotifications * 2)
      }
    },

    DISMISS_NOTIFICATION(state, notificationId) {
      const notification = state.notifications.find(n => n.id === notificationId)
      if (notification) {
        notification.dismissed = true
        notification.dismissedAt = new Date().toISOString()
      }
    },

    MARK_NOTIFICATION_read(state, notificationId) {
      const notification = state.notifications.find(n => n.id === notificationId)
      if (notification) {
        notification.read = true
        notification.readAt = new Date().toISOString()
      }
    },

    DISMISS_ALL_NOTIFICATIONS(state) {
      state.notifications.forEach(notification => {
        if (!notification.dismissed) {
          notification.dismissed = true
          notification.dismissedAt = new Date().toISOString()
        }
      })
    },

    CLEAR_OLD_NOTIFICATIONS(state) {
      const oneHourAgo = Date.now() - 60 * 60 * 1000
      state.notifications = state.notifications.filter(notification => {
        const notificationTime = new Date(notification.timestamp).getTime()
        return notificationTime > oneHourAgo || !notification.dismissed
      })
    },

    UPDATE_NOTIFICATION_SETTINGS(state, settings) {
      if (settings.maxNotifications !== undefined) {
        state.maxNotifications = settings.maxNotifications
      }
      if (settings.defaultTimeout !== undefined) {
        state.defaultTimeout = settings.defaultTimeout
      }
    }
  },

  actions: {
    addNotification({ commit, dispatch, _state }, notification) {
      // Validate notification structure
      if (!notification.title && !notification.message) {
        console.warn('Notification must have either title or message')
        return
      }

      // Set default type
      if (!notification.type) {
        notification.type = 'info'
      }

      // Set default timeout and persistent flag based on type BEFORE mutation
      if (!notification.timeout && notification.type !== 'emergency') {
        switch (notification.type) {
        case 'error':
          notification.timeout = 3000
          break
        case 'warning':
          notification.timeout = 3000
          break
        case 'success':
          notification.timeout = 3000
          break
        case 'info':
        default:
          notification.timeout = 3000
          break
        }
      }

      if (notification.type === 'emergency') {
        notification.timeout = 0
        notification.persistent = true
      }

      // Generate unique ID before mutation so we can use it for timeout
      const notificationId = Date.now() + Math.random()
      const notificationWithId = {
        id: notificationId,
        ...notification
      }

      // Add notification
      commit('ADD_NOTIFICATION', notificationWithId)

      // Auto-dismiss after timeout (unless persistent)
      if (!notificationWithId.persistent && notificationWithId.timeout > 0) {
        setTimeout(() => {
          dispatch('dismissNotification', notificationId)
        }, notificationWithId.timeout)
      }

      // Log to console for debugging
      const logLevel = notificationWithId.type === 'error'
        ? 'error'
        : notificationWithId.type === 'warning' ? 'warn' : 'log'
      console[logLevel](`Notification [${notificationWithId.type}]:`, notificationWithId.title || notificationWithId.message)

      return notificationWithId
    },

    dismissNotification({ commit }, notificationId) {
      commit('DISMISS_NOTIFICATION', notificationId)
    },

    markAsRead({ commit }, notificationId) {
      commit('MARK_NOTIFICATION_read', notificationId)
    },

    dismissAll({ commit }) {
      commit('DISMISS_ALL_NOTIFICATIONS')
    },

    clearOld({ commit }) {
      commit('CLEAR_OLD_NOTIFICATIONS')
    },

    // Convenience methods for common notification types
    showSuccess({ dispatch }, message) {
      return dispatch('addNotification', {
        type: 'success',
        title: 'Success',
        message,
        timeout: 3000
      })
    },

    showError({ dispatch }, message) {
      return dispatch('addNotification', {
        type: 'error',
        title: 'Error',
        message,
        timeout: 3000
      })
    },

    showWarning({ dispatch }, message) {
      return dispatch('addNotification', {
        type: 'warning',
        title: 'Warning',
        message,
        timeout: 3000
      })
    },

    showInfo({ dispatch }, message) {
      return dispatch('addNotification', {
        type: 'info',
        title: 'Information',
        message,
        timeout: 3000
      })
    },

    // System-level notifications
    showConnectionStatus({ dispatch }, isConnected) {
      if (isConnected) {
        return dispatch('showSuccess', 'Connected to server')
      } else {
        return dispatch('showError', 'Disconnected from server')
      }
    },

    showRadarStatus({ dispatch }, { isActive, source = 'local' }) {
      const sourceLabel = source === 'pico' ? 'Pico' : 'Local'
      if (isActive) {
        return dispatch('showSuccess', `${sourceLabel} radar started`)
      } else {
        return dispatch('showInfo', `${sourceLabel} radar stopped`)
      }
    },

    showServoStatus({ dispatch }, { isActive, position }) {
      if (isActive) {
        return dispatch('showSuccess', `Servo activated at ${position}°`)
      } else {
        return dispatch('showInfo', 'Servo deactivated')
      }
    },

    // Batch operations
    addMultiple({ dispatch }, notifications) {
      return Promise.all(
        notifications.map(notification => dispatch('addNotification', notification))
      )
    },

    // Maintenance
    performMaintenance({ dispatch }) {
      dispatch('clearOld')
    },

    // Settings management
    updateSettings({ commit }, settings) {
      commit('UPDATE_NOTIFICATION_SETTINGS', settings)

      // Save to localStorage
      try {
        localStorage.setItem('notificationSettings', JSON.stringify(settings))
      } catch (error) {
        console.warn('Failed to save notification settings:', error)
      }
    },

    loadSettings({ commit }) {
      try {
        const saved = localStorage.getItem('notificationSettings')
        if (saved) {
          const settings = JSON.parse(saved)
          commit('UPDATE_NOTIFICATION_SETTINGS', settings)
        }
      } catch (error) {
        console.warn('Failed to load notification settings:', error)
      }
    }
  }
}
