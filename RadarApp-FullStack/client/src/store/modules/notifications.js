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
      const newNotification = {
        id: Date.now() + Math.random(),
        timestamp: new Date().toISOString(),
        dismissed: false,
        read: false,
        ...notification
      }

      // Set default timeout and persistent flag based on type
      if (!newNotification.timeout) {
        switch (newNotification.type) {
        case 'emergency':
          newNotification.timeout = 0 // No auto-dismiss for emergencies
          newNotification.persistent = true
          break
        case 'error':
          newNotification.timeout = 10000 // 10 seconds for errors
          break
        case 'warning':
          newNotification.timeout = 7000 // 7 seconds for warnings
          break
        case 'success':
          newNotification.timeout = 4000 // 4 seconds for success
          break
        case 'info':
        default:
          newNotification.timeout = state.defaultTimeout || 5000 // 5 seconds default
          break
        }
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

    MARK_NOTIFICATION_READ(state, notificationId) {
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
    addNotification({ commit, dispatch }, notification) {
      // Validate notification structure
      if (!notification.title && !notification.message) {
        console.warn('Notification must have either title or message')
        return
      }

      // Set default type
      if (!notification.type) {
        notification.type = 'info'
      }

      // Add notification
      commit('ADD_NOTIFICATION', notification)

      // Auto-dismiss after timeout (unless persistent)
      if (!notification.persistent && notification.timeout > 0) {
        setTimeout(() => {
          dispatch('dismissNotification', notification.id || Date.now())
        }, notification.timeout)
      }

      // Log to console for debugging
      const logLevel = notification.type === 'error'
        ? 'error'
        : notification.type === 'warning' ? 'warn' : 'log'
      console[logLevel](`Notification [${notification.type}]:`, notification.title || notification.message)

      return notification
    },

    dismissNotification({ commit }, notificationId) {
      commit('DISMISS_NOTIFICATION', notificationId)
    },

    markAsRead({ commit }, notificationId) {
      commit('MARK_NOTIFICATION_READ', notificationId)
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
        timeout: 4000
      })
    },

    showError({ dispatch }, message) {
      return dispatch('addNotification', {
        type: 'error',
        title: 'Error',
        message,
        timeout: 10000
      })
    },

    showWarning({ dispatch }, message) {
      return dispatch('addNotification', {
        type: 'warning',
        title: 'Warning',
        message,
        timeout: 7000
      })
    },

    showInfo({ dispatch }, message) {
      return dispatch('addNotification', {
        type: 'info',
        title: 'Information',
        message,
        timeout: 5000
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
