export default {
  namespaced: true,

  state: {
    picoConnected: false,
    picoRadarData: [],
    picoServoStatus: {
      position: 90,
      is_active: false,
      target_angle: 90
    },
    picoStatus: {
      radar_active: false,
      last_ping: null,
      voltage: null,
      temperature: null
    },
    isReceivingData: false,
    stats: {
      totalScans: 0,
      detectionsCount: 0,
      commandsSent: 0,
      lastResponseTime: null
    },
    commandQueue: [],
    lastCommand: null,
    responseTimeout: 5000
  },

  getters: {
    picoHealth: (state) => {
      if (!state.picoConnected) return 'disconnected'

      const lastPing = state.picoStatus.last_ping
      if (!lastPing) return 'unknown'

      const timeSinceLastPing = Date.now() - new Date(lastPing).getTime()

      if (timeSinceLastPing < 5000) return 'excellent'
      if (timeSinceLastPing < 15000) return 'good'
      if (timeSinceLastPing < 30000) return 'fair'
      return 'poor'
    },

    recentPicoDetections: (state) => {
      const fiveMinutesAgo = Date.now() - 5 * 60 * 1000
      return state.picoRadarData.filter(data =>
        data.detected &&
        new Date(data.timestamp).getTime() > fiveMinutesAgo
      )
    },

    picoPerformanceMetrics: (state) => {
      const lastHour = Date.now() - 60 * 60 * 1000
      const recentData = state.picoRadarData.filter(data =>
        new Date(data.timestamp).getTime() > lastHour
      )

      return {
        dataRate: recentData.length / 60, // per minute
        detectionRate: recentData.filter(d => d.detected).length / 60,
        avgResponseTime: state.stats.lastResponseTime || 0,
        reliability: state.picoConnected && recentData.length > 0 ? 'good' : 'poor'
      }
    }
  },

  mutations: {
    SET_PICO_CONNECTION(state, isConnected) {
      state.picoConnected = isConnected
      if (!isConnected) {
        state.isReceivingData = false
        state.picoStatus.radar_active = false
      }
    },

    SET_RECEIVING_DATA(state, isReceiving) {
      state.isReceivingData = isReceiving
    },

    ADD_PICO_RADAR_DATA(state, data) {
      // Add timestamp and source if not provided
      if (!data.timestamp) {
        data.timestamp = new Date().toISOString()
      }
      data.source = 'pico'

      state.picoRadarData.push(data)

      // Update stats
      state.stats.totalScans++
      if (data.detected) {
        state.stats.detectionsCount++
      }

      // Keep only last 500 readings for performance
      if (state.picoRadarData.length > 500) {
        state.picoRadarData = state.picoRadarData.slice(-500)
      }

      // Update receiving status
      if (!state.isReceivingData) {
        state.isReceivingData = true
      }
    },

    UPDATE_SERVO_STATUS(state, status) {
      state.picoServoStatus = { ...state.picoServoStatus, ...status }
    },

    UPDATE_PICO_STATUS(state, status) {
      state.picoStatus = {
        ...state.picoStatus,
        ...status,
        last_ping: new Date().toISOString()
      }
    },

    ADD_COMMAND_TO_QUEUE(state, command) {
      state.commandQueue.push({
        ...command,
        id: Date.now() + Math.random(),
        timestamp: new Date().toISOString(),
        status: 'pending'
      })
    },

    UPDATE_COMMAND_STATUS(state, { commandId, status, response }) {
      const command = state.commandQueue.find(cmd => cmd.id === commandId)
      if (command) {
        command.status = status
        command.response = response
        command.completedAt = new Date().toISOString()
      }
    },

    SET_LAST_COMMAND(state, command) {
      state.lastCommand = command
      state.stats.commandsSent++
    },

    SET_RESPONSE_TIME(state, responseTime) {
      state.stats.lastResponseTime = responseTime
    },

    CLEAR_PICO_DATA(state) {
      state.picoRadarData = []
      state.stats = {
        totalScans: 0,
        detectionsCount: 0,
        commandsSent: state.stats.commandsSent,
        lastResponseTime: state.stats.lastResponseTime
      }
    },

    REMOVE_OLD_COMMANDS(state) {
      const tenMinutesAgo = Date.now() - 10 * 60 * 1000
      state.commandQueue = state.commandQueue.filter(cmd =>
        new Date(cmd.timestamp).getTime() > tenMinutesAgo
      )
    }
  },

  actions: {
    async sendCommand({ commit, dispatch, state, rootState: _rootState }, { command, params = null }) {
      try {
        if (!state.picoConnected) {
          throw new Error('Pico is not connected')
        }

        const commandData = {
          command,
          params,
          timestamp: new Date().toISOString()
        }

        // Add to command queue
        commit('ADD_COMMAND_TO_QUEUE', commandData)
        commit('SET_LAST_COMMAND', commandData)

        const startTime = Date.now()

        // Send via WebSocket to server
        await dispatch('connection/sendMessage', {
          type: 'pico_command',
          data: commandData
        }, { root: true })

        // Calculate response time (will be updated when response comes back)
        const responseTime = Date.now() - startTime
        commit('SET_RESPONSE_TIME', responseTime)

        return commandData
      } catch (error) {
        throw new Error(`Failed to send Pico command: ${error.message}`)
      }
    },

    async controlServo({ dispatch }, action) {
      try {
        const commands = {
          activate: { command: 'servo_activate' },
          deactivate: { command: 'servo_deactivate' },
          position: { command: 'servo_position', params: { angle: action.angle } },
          sweep: { command: 'servo_sweep', params: { start: action.start, end: action.end, speed: action.speed } }
        }

        const commandData = commands[action] || commands[action.type]
        if (!commandData) {
          throw new Error(`Unknown servo action: ${action}`)
        }

        return await dispatch('sendCommand', commandData)
      } catch (error) {
        throw new Error(`Servo control failed: ${error.message}`)
      }
    },

    async requestStatus({ dispatch }) {
      try {
        return await dispatch('sendCommand', {
          command: 'get_status'
        })
      } catch (error) {
        throw new Error(`Status request failed: ${error.message}`)
      }
    },

    async startPicoRadar({ dispatch }) {
      try {
        return await dispatch('sendCommand', {
          command: 'radar_start'
        })
      } catch (error) {
        throw new Error(`Failed to start Pico radar: ${error.message}`)
      }
    },

    async stopPicoRadar({ dispatch }) {
      try {
        return await dispatch('sendCommand', {
          command: 'radar_stop'
        })
      } catch (error) {
        throw new Error(`Failed to stop Pico radar: ${error.message}`)
      }
    },

    async configurePicoRadar({ dispatch }, config) {
      try {
        return await dispatch('sendCommand', {
          command: 'radar_config',
          params: config
        })
      } catch (error) {
        throw new Error(`Failed to configure Pico radar: ${error.message}`)
      }
    },

    processPicoMessage({ commit, dispatch }, message) {
      try {
        switch (message.type) {
        case 'radar_data':
          commit('ADD_PICO_RADAR_DATA', message.data)
          break

        case 'servo_status':
          commit('UPDATE_SERVO_STATUS', message.data)
          break

        case 'pico_status':
          commit('UPDATE_PICO_STATUS', message.data)
          break

        case 'command_response':
          if (message.data.commandId) {
            commit('UPDATE_COMMAND_STATUS', {
              commandId: message.data.commandId,
              status: message.data.success ? 'completed' : 'failed',
              response: message.data
            })
          }
          break

        case 'error':
          dispatch('notifications/addNotification', {
            type: 'error',
            title: 'Pico Error',
            message: message.data.message || 'Unknown Pico error'
          }, { root: true })
          break

        default:
          console.warn('Unknown Pico message type:', message.type)
        }
      } catch (error) {
        console.error('Failed to process Pico message:', error)
      }
    },

    handlePicoConnection({ commit, dispatch }, isConnected) {
      commit('SET_PICO_CONNECTION', isConnected)

      if (isConnected) {
        dispatch('notifications/addNotification', {
          type: 'success',
          title: 'Pico Connected',
          message: 'Raspberry Pi Pico is now connected via UART'
        }, { root: true })

        // Request initial status
        setTimeout(() => {
          dispatch('requestStatus')
        }, 1000)
      } else {
        dispatch('notifications/addNotification', {
          type: 'warning',
          title: 'Pico Disconnected',
          message: 'Connection to Raspberry Pi Pico lost'
        }, { root: true })
      }
    },

    clearPicoData({ commit }) {
      commit('CLEAR_PICO_DATA')
    },

    // Periodic maintenance
    performMaintenance({ commit }) {
      commit('REMOVE_OLD_COMMANDS')
    },

    // Emergency stop - stops all Pico operations
    async emergencyStop({ dispatch }) {
      try {
        await Promise.all([
          dispatch('stopPicoRadar'),
          dispatch('controlServo', 'deactivate')
        ])

        dispatch('notifications/addNotification', {
          type: 'warning',
          title: 'Emergency Stop',
          message: 'All Pico operations have been stopped'
        }, { root: true })
      } catch (error) {
        throw new Error(`Emergency stop failed: ${error.message}`)
      }
    }
  }
}
