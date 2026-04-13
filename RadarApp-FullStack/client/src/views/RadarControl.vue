<template>
  <div class="radar-control-view">
    <div class="row g-4">
      <!-- Radar Display Column -->
      <div class="col-lg-8">
        <div class="card card-custom">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="card-title mb-0">
              <i class="fas fa-radar-dish me-2"></i>
              Radar Display
            </h5>
            <div class="radar-controls">
              <button
                @click="toggleLocalRadar"
                :class="['btn', 'btn-sm', 'me-2', localRadarActive ? 'btn-success' : 'btn-outline-secondary']"
                :disabled="!allConnected"
              >
                <i class="fas fa-satellite-dish me-1"></i>
                Local Radar
              </button>
              <button
                @click="togglePicoRadar"
                :class="['btn', 'btn-sm', 'me-2', picoRadarActive ? 'btn-success' : 'btn-outline-secondary']"
                :disabled="!allConnected"
              >
                <i class="fas fa-microchip me-1"></i>
                Pico Radar
              </button>
              <button
                @click="emergencyStop"
                class="btn btn-sm btn-danger"
                :disabled="!allConnected"
              >
                <i class="fas fa-stop me-1"></i>
                EMERGENCY STOP
              </button>
            </div>
          </div>
          <div class="card-body p-0">
            <RadarDisplay
              :radar-data="combinedRadarData"
              :is-scanning="isScanning"
              :range="radarRange"
            />
          </div>
        </div>

        <!-- Detection Log -->
        <div class="card card-custom mt-4">
          <div class="card-header">
            <h6 class="card-title mb-0">
              <i class="fas fa-list me-2"></i>
              Recent Detections
            </h6>
          </div>
          <div class="card-body">
            <DetectionLog :detections="recentDetections" />
          </div>
        </div>
      </div>

      <!-- Control Panel Column -->
      <div class="col-lg-4">
        <!-- Radar Status -->
        <div class="card card-custom mb-4">
          <div class="card-header">
            <h6 class="card-title mb-0">
              <i class="fas fa-info-circle me-2"></i>
              Radar Status
            </h6>
          </div>
          <div class="card-body">
            <div class="status-grid">
              <div class="status-item">
                <span class="status-label">Local Radar:</span>
                <span :class="['badge', localRadarActive ? 'bg-success' : 'bg-secondary']">
                  {{ localRadarActive ? 'Active' : 'Inactive' }}
                </span>
              </div>
              <div class="status-item">
                <span class="status-label">Pico Radar:</span>
                <span :class="['badge', picoRadarActive ? 'bg-success' : 'bg-secondary']">
                  {{ picoRadarActive ? 'Active' : 'Inactive' }}
                </span>
              </div>
              <div class="status-item">
                <span class="status-label">Total Scans:</span>
                <span class="badge bg-info">{{ totalScans }}</span>
              </div>
              <div class="status-item">
                <span class="status-label">Detections:</span>
                <span class="badge bg-warning">{{ totalDetections }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Radar Configuration -->
        <div class="card card-custom mb-4">
          <div class="card-header">
            <h6 class="card-title mb-0">
              <i class="fas fa-sliders-h me-2"></i>
              Configuration
            </h6>
          </div>
          <div class="card-body">
            <div class="mb-3">
              <label class="form-label">Detection Range (m)</label>
              <input
                v-model.number="radarRange"
                type="range"
                class="form-range"
                min="10"
                max="500"
                step="10"
                @change="updateRadarConfig"
              >
              <div class="d-flex justify-content-between text-muted small">
                <span>10m</span>
                <span class="fw-bold">{{ radarRange }}m</span>
                <span>500m</span>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Sensitivity</label>
              <input
                v-model.number="sensitivity"
                type="range"
                class="form-range"
                min="0"
                max="100"
                step="5"
                @change="updateRadarConfig"
              >
              <div class="d-flex justify-content-between text-muted small">
                <span>Low</span>
                <span class="fw-bold">{{ sensitivity }}%</span>
                <span>High</span>
              </div>
            </div>

            <div class="mb-3">
              <label class="form-label">Scan Interval (ms)</label>
              <select v-model="scanInterval" class="form-select" @change="updateRadarConfig">
                <option value="50">50ms (Fast)</option>
                <option value="100">100ms (Normal)</option>
                <option value="250">250ms (Slow)</option>
                <option value="500">500ms (Very Slow)</option>
              </select>
            </div>

            <button @click="resetRadarConfig" class="btn btn-outline-secondary btn-sm w-100">
              <i class="fas fa-undo me-1"></i>
              Reset to Defaults
            </button>
          </div>
        </div>

        <!-- Servo Control -->
        <div class="card card-custom mb-4" v-if="picoConnected">
          <div class="card-header">
            <h6 class="card-title mb-0">
              <i class="fas fa-cog me-2"></i>
              Servo Control
            </h6>
          </div>
          <div class="card-body">
            <div v-if="!allConnected" class="alert alert-warning" role="alert">
              ⚠️ Servo control disabled. All connections required (Server, Serial, Pico).
            </div>
            <div class="mb-3">
              <div class="servo-status mb-3">
                <span class="status-label">Status:</span>
                <span :class="['badge', servoActive ? 'bg-success' : 'bg-secondary', 'ms-2']">
                  {{ servoActive ? 'Extended' : 'Retracted' }}
                </span>
                <span class="status-label ms-3">Position:</span>
                <span class="badge bg-primary ms-2">{{ servoPosition }}°</span>
              </div>

              <div class="d-grid gap-2" style="grid-template-columns: 1fr 1fr;">
                <button
                  @click="openServo"
                  class="btn btn-success"
                  :disabled="!allConnected"
                >
                  <i class="fas fa-arrow-right me-1"></i>
                  Open
                </button>
                <button
                  @click="closeServo"
                  class="btn btn-warning"
                  :disabled="!allConnected"
                >
                  <i class="fas fa-arrow-left me-1"></i>
                  Close
                </button>
              </div>

              <button @click="refreshServoStatus" class="btn btn-outline-info btn-sm w-100 mt-2" :disabled="!allConnected">
                <i class="fas fa-sync me-1"></i>
                Refresh Status
              </button>
            </div>
          </div>
        </div>

        <!-- Stepper Motor Raise/Lower -->
        <div class="card">
          <div class="card-body">
            <h5 class="card-title">Stepper Motor Control</h5>
            <div v-if="!allConnected" class="alert alert-warning" role="alert">
              ⚠️ Stepper control disabled. All connections required (Server, Serial, Pico).
            </div>
            <div v-if="allConnected">
              <div class="mb-3">
                <span class="badge" :class="targetPosition === 360 ? 'bg-success' : targetPosition === 0 ? 'bg-warning' : 'bg-info'">
                  {{ targetPosition === 360 ? '☝️ Up' : targetPosition === 0 ? '👇 Down' : `Position: ${targetPosition}°` }}
                </span>
              </div>
              <div class="d-grid gap-2" style="grid-template-columns: 1fr 1fr;">
                <button
                  @click="raiseRadar"
                  class="btn btn-success btn-lg"
                >
                  <i class="fas fa-arrow-up me-1"></i>
                  Raise
                </button>
                <button
                  @click="lowerRadar"
                  class="btn btn-warning btn-lg"
                >
                  <i class="fas fa-arrow-down me-1"></i>
                  Lower
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Data Export -->
        <div class="card card-custom">
          <div class="card-header">
            <h6 class="card-title mb-0">
              <i class="fas fa-download me-2"></i>
              Data Export
            </h6>
          </div>
          <div class="card-body">
            <div class="d-grid gap-2">
              <button @click="exportRadarData" class="btn btn-outline-primary btn-sm">
                <i class="fas fa-file-csv me-1"></i>
                Export CSV
              </button>
              <button @click="clearRadarData" class="btn btn-outline-danger btn-sm">
                <i class="fas fa-trash me-1"></i>
                Clear Data
              </button>
            </div>

            <small class="text-muted d-block mt-2">
              <i class="fas fa-info-circle me-1"></i>
              {{ radarDataCount }} data points collected
            </small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import RadarDisplay from '../components/RadarDisplay.vue'
import DetectionLog from '../components/DetectionLog.vue'

export default {
  name: 'RadarControl',
  components: {
    RadarDisplay,
    DetectionLog
  },

  data() {
    return {
      radarRange: 100,
      sensitivity: 50,
      scanInterval: 100,
      sweepAngle: 0,
      sweepDirection: 1,
      sweepInterval: null
    }
  },

  computed: {
    ...mapState('connection', ['isConnected']),
    ...mapState('radar', ['isScanning', 'radarData', 'stats']),
    ...mapState('pico', ['picoConnected', 'picoRadarData', 'picoServoStatus']),

    allConnected() {
      return this.$store.getters['connection/allConnected']
    },

    localRadarActive() {
      return this.isScanning
    },

    picoRadarActive() {
      return this.picoConnected && this.$store.state.pico.isReceivingData
    },

    combinedRadarData() {
      // Combine local and Pico radar data for display
      const combined = [...this.radarData]

      if (this.picoRadarData && this.picoRadarData.length > 0) {
        // Add Pico data with different styling/color
        const picoData = this.picoRadarData.map(data => ({
          ...data,
          source: 'pico',
          color: '#ff6b35'
        }))
        combined.push(...picoData)
      }

      return combined.slice(-100) // Keep last 100 readings for performance
    },

    recentDetections() {
      // Get recent detections from both sources
      const localDetections = this.radarData
        .filter(d => d.detected)
        .slice(-20)
        .map(d => ({ ...d, source: 'local' }))

      const picoDetections = (this.picoRadarData || [])
        .filter(d => d.detected)
        .slice(-20)
        .map(d => ({ ...d, source: 'pico' }))

      return [...localDetections, ...picoDetections]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 20)
    },

    totalScans() {
      return this.stats.totalScans + (this.$store.state.pico.stats?.totalScans || 0)
    },

    totalDetections() {
      return this.stats.detectionsCount + (this.$store.state.pico.stats?.detectionsCount || 0)
    },

    picoServoPosition() {
      return this.picoServoStatus?.position || 90
    },

    picoServoActive() {
      return this.picoServoStatus?.is_active || false
    },

    servoActive() {
      return this.$store.state.actuator?.status?.isOpen || false
    },

    servoPosition() {
      return this.$store.state.actuator?.status?.position || 90
    },

    targetPosition() {
      return this.$store.state.stepper?.status?.targetPosition || 0
    },

    radarDataCount() {
      return this.radarData.length + (this.picoRadarData?.length || 0)
    }
  },

  mounted() {
    this.startSweepAnimation()
    this.loadRadarSettings()
  },

  beforeUnmount() {
    this.stopSweepAnimation()
  },

  methods: {
    ...mapActions('radar', [
      'startRadar', 'stopRadar', 'updateConfiguration', 'clearData', 'exportData'
    ]),
    ...mapActions('actuator', ['open', 'close', 'fetchStatus']),
    ...mapActions('pico', [
      'sendCommand', 'controlServo', 'requestStatus'
    ]),
    ...mapActions('notifications', ['addNotification']),

    async toggleLocalRadar() {
      try {
        if (this.localRadarActive) {
          await this.stopRadar()
        } else {
          await this.startRadar()
        }
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Radar Control Error',
          message: error.message
        })
      }
    },

    async togglePicoRadar() {
      try {
        if (this.picoRadarActive) {
          await this.sendCommand({ command: 'radar_stop' })
        } else {
          await this.sendCommand({ command: 'radar_start' })
        }
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Pico Radar Error',
          message: error.message
        })
      }
    },

    async activatePicoServo() {
      try {
        const action = this.picoServoActive ? 'deactivate' : 'activate'
        await this.controlServo(action)

        this.addNotification({
          type: 'success',
          title: 'Servo Control',
          message: `Pico servo ${action}d successfully`
        })
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Servo Control Error',
          message: error.message
        })
      }
    },

    async requestPicoStatus() {
      try {
        await this.requestStatus()
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Status Request Error',
          message: error.message
        })
      }
    },

    async updateRadarConfig() {
      try {
        const config = {
          scanInterval: this.scanInterval,
          detectionThreshold: this.sensitivity,
          maxDistance: this.radarRange
        }

        // Update local radar
        await this.updateConfiguration(config)

        // Update Pico radar if connected
        if (this.picoConnected) {
          await this.sendCommand({
            command: 'radar_config',
            params: config
          })
        }

        // Save settings
        this.saveRadarSettings()
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Configuration Error',
          message: error.message
        })
      }
    },

    resetRadarConfig() {
      this.radarRange = 100
      this.sensitivity = 50
      this.scanInterval = 100
      this.updateRadarConfig()
    },

    async exportRadarData() {
      try {
        await this.exportData()
        this.addNotification({
          type: 'success',
          title: 'Export Complete',
          message: 'Radar data exported successfully'
        })
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Export Error',
          message: error.message
        })
      }
    },

    async clearRadarData() {
      try {
        await this.clearData()
        this.addNotification({
          type: 'info',
          title: 'Data Cleared',
          message: 'All radar data has been cleared'
        })
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Clear Error',
          message: error.message
        })
      }
    },

    startSweepAnimation() {
      this.sweepInterval = setInterval(() => {
        this.sweepAngle += this.sweepDirection * 2
        if (this.sweepAngle >= 360) {
          this.sweepAngle = 0
        }
      }, 50)
    },

    stopSweepAnimation() {
      if (this.sweepInterval) {
        clearInterval(this.sweepInterval)
        this.sweepInterval = null
      }
    },

    loadRadarSettings() {
      const saved = localStorage.getItem('radarSettings')
      if (saved) {
        try {
          const settings = JSON.parse(saved)
          this.radarRange = settings.radarRange || 100
          this.sensitivity = settings.sensitivity || 50
          this.scanInterval = settings.scanInterval || 100
        } catch (error) {
          console.warn('Failed to load radar settings:', error)
        }
      }
    },

    saveRadarSettings() {
      const settings = {
        radarRange: this.radarRange,
        sensitivity: this.sensitivity,
        scanInterval: this.scanInterval
      }
      localStorage.setItem('radarSettings', JSON.stringify(settings))
    },

    async openServo() {
      try {
        await this.open()
        this.addNotification({
          type: 'success',
          title: 'Servo Control',
          message: 'Servo opened successfully'
        })
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Servo Error',
          message: `Failed: ${error.message}`
        })
      }
    },

    async closeServo() {
      try {
        await this.close()
        this.addNotification({
          type: 'success',
          title: 'Servo Control',
          message: 'Servo closed successfully'
        })
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Servo Error',
          message: `Failed: ${error.message}`
        })
      }
    },

    async raiseRadar() {
      try {
        await this.$store.dispatch('stepper/raise')
        await this.$store.dispatch('actuator/open')
      } catch (error) {
        console.error('Raise failed:', error)
      }
    },

    async lowerRadar() {
      try {
        await this.$store.dispatch('stepper/lower')
        await this.$store.dispatch('actuator/close')
      } catch (error) {
        console.error('Lower failed:', error)
      }
    },

    async refreshServoStatus() {
      try {
        await this.fetchStatus()
        this.addNotification({
          type: 'success',
          title: 'Servo Status',
          message: 'Status refreshed'
        })
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Status Error',
          message: `Failed: ${error.message}`
        })
      }
    },

    async emergencyStop() {
      try {
        if (confirm('Are you sure you want to trigger EMERGENCY STOP? This will stop all radar operations immediately!')) {
          await this.stopRadar()
          await this.close()
          this.addNotification({
            type: 'emergency',
            title: '🛑 EMERGENCY STOP ACTIVATED',
            message: 'All systems halted. Click "Clear" to acknowledge.',
            persistent: true
          })
        }
      } catch (error) {
        this.addNotification({
          type: 'error',
          title: 'Emergency Stop Error',
          message: `Failed: ${error.message}`,
          timeout: 5000
        })
      }
    }
  }
}
</script>

<style scoped>
.radar-control-view {
  min-height: calc(100vh - 120px);
}

.status-grid {
  display: grid;
  gap: 0.75rem;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.375rem;
}

.status-label {
  font-weight: 500;
  color: #6c757d;
}

.servo-status {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.radar-controls {
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .radar-controls {
    flex-direction: column;
    gap: 0.25rem;
  }

  .servo-status {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
