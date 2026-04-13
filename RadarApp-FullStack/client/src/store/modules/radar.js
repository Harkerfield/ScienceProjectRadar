import apiService from '../../services/apiService'

export default {
  namespaced: true,

  state: {
    isScanning: false,
    radarData: [],
    currentSweepAngle: 0,
    configuration: {
      scanInterval: 100,
      detectionThreshold: 50,
      maxDistance: 100
    },
    stats: {
      totalScans: 0,
      detectionsCount: 0,
      lastScanTime: null,
      avgDetectionRate: 0
    },
    calibration: {
      isCalibrated: false,
      baselineNoise: 0,
      sensitivityMap: {}
    },
    errorLog: []
  },

  getters: {
    currentSweepAngle: (state) => state.currentSweepAngle,

    activeDetections: (state) => {
      const fiveMinutesAgo = Date.now() - 5 * 60 * 1000
      return state.radarData.filter(data =>
        data.detected &&
        new Date(data.timestamp).getTime() > fiveMinutesAgo
      )
    },

    detectionsByRange: (state) => {
      const ranges = {
        close: { min: 0, max: 50, count: 0 },
        medium: { min: 50, max: 150, count: 0 },
        far: { min: 150, max: 500, count: 0 }
      }

      state.radarData.forEach(data => {
        if (data.detected) {
          const distance = data.distance || 0
          if (distance <= ranges.close.max) ranges.close.count++
          else if (distance <= ranges.medium.max) ranges.medium.count++
          else ranges.far.count++
        }
      })

      return ranges
    },

    recentPerformance: (state) => {
      const lastHour = Date.now() - 60 * 60 * 1000
      const recentData = state.radarData.filter(data =>
        new Date(data.timestamp).getTime() > lastHour
      )

      return {
        scans: recentData.length,
        detections: recentData.filter(d => d.detected).length,
        avgSignalStrength: recentData.reduce((acc, d) => acc + (d.strength || 0), 0) / recentData.length || 0
      }
    }
  },

  mutations: {
    SET_SWEEP_ANGLE(state, angle) {
      state.currentSweepAngle = angle % 360
    },

    SET_SCANNING_STATE(state, isScanning) {
      state.isScanning = isScanning
      if (isScanning) {
        state.stats.lastScanTime = new Date().toISOString()
      }
    },

    ADD_RADAR_DATA(state, data) {
      // Add timestamp if not provided
      if (!data.timestamp) {
        data.timestamp = new Date().toISOString()
      }

      state.radarData.push(data)

      // Update stats
      state.stats.totalScans++
      if (data.detected) {
        state.stats.detectionsCount++
      }

      // Keep only last 1000 readings for performance
      if (state.radarData.length > 1000) {
        state.radarData = state.radarData.slice(-1000)
      }

      // Update detection rate
      const recentDetections = state.radarData.slice(-100).filter(d => d.detected).length
      state.stats.avgDetectionRate = (recentDetections / Math.min(100, state.radarData.length)) * 100
    },

    UPDATE_CONFIGURATION(state, config) {
      state.configuration = { ...state.configuration, ...config }
    },

    SET_CALIBRATION(state, calibration) {
      state.calibration = { ...state.calibration, ...calibration }
    },

    CLEAR_RADAR_DATA(state) {
      state.radarData = []
      state.stats = {
        totalScans: 0,
        detectionsCount: 0,
        lastScanTime: null,
        avgDetectionRate: 0
      }
    },

    ADD_error(state, error) {
      state.errorLog.push({
        timestamp: new Date().toISOString(),
        error: error.message || error,
        type: error.type || 'radar_error'
      })

      // Keep only last 50 errors
      if (state.errorLog.length > 50) {
        state.errorLog = state.errorLog.slice(-50)
      }
    }
  },

  actions: {
    async startRadar({ commit, dispatch, state, rootState }) {
      try {
        if (state.isScanning) {
          throw new Error('Radar is already scanning')
        }

        if (!rootState.connection.isConnected) {
          throw new Error('Not connected to server')
        }

        // Send start command to server
        await dispatch('connection/sendMessage', {
          type: 'radar_start',
          data: state.configuration
        }, { root: true })

        commit('SET_SCANNING_STATE', true)

        dispatch('notifications/addNotification', {
          type: 'success',
          title: 'Radar Started',
          message: 'Local radar scanning initiated'
        }, { root: true })
      } catch (error) {
        commit('ADD_error', error)
        throw error
      }
    },

    async stopRadar({ commit, dispatch, state, rootState: _rootState }) {
      try {
        if (!state.isScanning) {
          throw new Error('Radar is not currently scanning')
        }

        // Send stop command to server
        await dispatch('connection/sendMessage', {
          type: 'radar_stop'
        }, { root: true })

        commit('SET_SCANNING_STATE', false)

        dispatch('notifications/addNotification', {
          type: 'info',
          title: 'Radar Stopped',
          message: 'Local radar scanning stopped'
        }, { root: true })
      } catch (error) {
        commit('ADD_error', error)
        throw error
      }
    },

    async updateConfiguration({ commit, dispatch, state }, config) {
      try {
        // Validate configuration
        if (config.scanInterval && (config.scanInterval < 10 || config.scanInterval > 5000)) {
          throw new Error('Scan interval must be between 10ms and 5000ms')
        }

        if (config.detectionThreshold && (config.detectionThreshold < 0 || config.detectionThreshold > 100)) {
          throw new Error('Detection threshold must be between 0 and 100')
        }

        if (config.maxDistance && (config.maxDistance < 10 || config.maxDistance > 1000)) {
          throw new Error('Max distance must be between 10m and 1000m')
        }

        commit('UPDATE_CONFIGURATION', config)

        // Send updated config to server if scanning
        if (state.isScanning) {
          await dispatch('connection/sendMessage', {
            type: 'radar_config',
            data: state.configuration
          }, { root: true })
        }

        // Save to localStorage
        localStorage.setItem('radarConfig', JSON.stringify(state.configuration))
      } catch (error) {
        commit('ADD_error', error)
        throw error
      }
    },

    updateSweepAngle({ commit }, angle) {
      // Update sweep angle from stepper position (real-time from microcontroller)
      commit('SET_SWEEP_ANGLE', angle)
    },

    processRadarData({ commit }, data) {
      // Process incoming radar data from server
      try {
        // Validate data structure
        if (!data.timestamp) {
          data.timestamp = new Date().toISOString()
        }

        // Add source identifier
        data.source = data.source || 'local'

        // Process detection logic
        if (typeof data.detected === 'undefined' && data.strength !== undefined) {
          data.detected = data.strength > this.state.radar.configuration.detectionThreshold
        }

        commit('ADD_RADAR_DATA', data)
      } catch (error) {
        commit('ADD_error', { message: 'Failed to process radar data', type: 'data_processing' })
      }
    },

    async calibrateRadar({ commit, dispatch, state: _state }) {
      try {
        dispatch('notifications/addNotification', {
          type: 'info',
          title: 'Calibration Started',
          message: 'Calibrating radar baseline...'
        }, { root: true })

        // Send calibration command
        await dispatch('connection/sendMessage', {
          type: 'radar_calibrate'
        }, { root: true })

        // Calibration will be completed when server responds with baseline data
      } catch (error) {
        commit('ADD_error', error)
        throw error
      }
    },

    setCalibrationData({ commit }, calibrationData) {
      commit('SET_CALIBRATION', {
        isCalibrated: true,
        baselineNoise: calibrationData.baselineNoise || 0,
        sensitivityMap: calibrationData.sensitivityMap || {}
      })

      // Save calibration data
      localStorage.setItem('radarCalibration', JSON.stringify(calibrationData))
    },

    async exportData({ state }) {
      try {
        const dataToExport = {
          configuration: state.configuration,
          stats: state.stats,
          detections: state.radarData.filter(d => d.detected),
          exportTime: new Date().toISOString()
        }

        const dataStr = JSON.stringify(dataToExport, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })

        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `radar_data_${new Date().toISOString().split('T')[0]}.json`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)
      } catch (error) {
        throw new Error('Failed to export radar data')
      }
    },

    clearData({ commit }) {
      commit('CLEAR_RADAR_DATA')
      localStorage.removeItem('radarData')
    },

    loadPersistedData({ commit }) {
      try {
        // Load configuration
        const savedConfig = localStorage.getItem('radarConfig')
        if (savedConfig) {
          const config = JSON.parse(savedConfig)
          commit('UPDATE_CONFIGURATION', config)
        }

        // Load calibration
        const savedCalibration = localStorage.getItem('radarCalibration')
        if (savedCalibration) {
          const calibration = JSON.parse(savedCalibration)
          commit('SET_CALIBRATION', calibration)
        }
      } catch (error) {
        console.warn('Failed to load persisted radar data:', error)
      }
    },

    async fetchStatus({ commit }) {
      try {
        const response = await apiService.get('/device/radar/status')
        const data = response.data.data || response.data.response
        commit('ADD_RADAR_DATA', {
          range: data.range,
          velocity: data.velocity,
          confidence: data.confidence,
          movement: data.movement,
          detected: data.confidence > 0,
          timestamp: new Date().toISOString()
        })
        return data
      } catch (error) {
        commit('ADD_error', { message: `Failed to fetch radar status: ${error.message}`, type: 'api_error' })
        throw error
      }
    },

    async readRadar({ commit }) {
      try {
        const response = await apiService.post('/device/radar/read')
        const data = response.data.data || response.data.response
        commit('ADD_RADAR_DATA', {
          range: data.range,
          velocity: data.velocity,
          confidence: data.confidence,
          movement: data.movement,
          detected: data.confidence > 0,
          timestamp: new Date().toISOString()
        })
        return data
      } catch (error) {
        commit('ADD_error', { message: `Failed to read radar: ${error.message}`, type: 'api_error' })
        throw error
      }
    },

    async setRangeSimulation({ commit, dispatch }, centimeters) {
      try {
        const response = await apiService.post('/device/radar/set_range', { 
          args: { centimeters } 
        })
        commit('ADD_RADAR_DATA', {
          range: centimeters,
          timestamp: new Date().toISOString()
        })

        dispatch('notifications/addNotification', {
          type: 'info',
          title: 'Radar Range Set',
          message: `Simulated range set to ${centimeters}cm`
        }, { root: true })

        return response.data
      } catch (error) {
        commit('ADD_error', { message: `Failed to set range: ${error.message}`, type: 'api_error' })
        throw error
      }
    },

    async setVelocitySimulation({ commit, dispatch }, metersPerSecond) {
      try {
        const response = await apiService.post('/device/radar/set_velocity', { 
          args: { meters_per_second: metersPerSecond } 
        })
        commit('ADD_RADAR_DATA', {
          velocity: metersPerSecond,
          timestamp: new Date().toISOString()
        })

        dispatch('notifications/addNotification', {
          type: 'info',
          title: 'Radar Velocity Set',
          message: `Simulated velocity set to ${metersPerSecond}m/s`
        }, { root: true })

        return response.data
      } catch (error) {
        commit('ADD_error', { message: `Failed to set velocity: ${error.message}`, type: 'api_error' })
        throw error
      }
    },

    async ping({ commit }) {
      try {
        const response = await apiService.get('/device/radar/ping')
        return response.data
      } catch (error) {
        commit('ADD_error', { message: `Ping failed: ${error.message}`, type: 'api_error' })
        throw error
      }
    },

    async getInfo({ _commit }) {
      try {
        const response = await apiService.get('/device/radar/whoami')
        return response.data
      } catch (error) {
        console.error('Failed to get radar info:', error)
        throw error
      }
    }
  }
}
