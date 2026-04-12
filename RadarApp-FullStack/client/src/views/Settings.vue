<template>
  <div class="settings">
    <div class="page-header">
      <h1>Settings</h1>
      <button @click="resetToDefaults" class="btn btn-outline">
        Reset to Defaults
      </button>
    </div>

    <div class="settings-sections">
      <!-- Radar Settings -->
      <div class="card radar-settings">
        <h2>Radar Settings</h2>
        <div class="setting-group">
          <div class="setting-item">
            <label for="detectionRange">Detection Range (cm):</label>
            <input
              id="detectionRange"
              v-model.number="localSettings.radar.detectionRange"
              type="number"
              min="10"
              max="500"
            />
          </div>
          <div class="setting-item">
            <label for="sensitivity">Sensitivity:</label>
            <input
              id="sensitivity"
              v-model.number="localSettings.radar.sensitivity"
              type="range"
              min="1"
              max="10"
              step="1"
            />
            <span class="range-value">{{ localSettings.radar.sensitivity }}</span>
          </div>
          <div class="setting-item">
            <label for="scanSpeed">Scan Speed:</label>
            <select id="scanSpeed" v-model="localSettings.radar.scanSpeed">
              <option value="slow">Slow</option>
              <option value="medium">Medium</option>
              <option value="fast">Fast</option>
            </select>
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input
                v-model="localSettings.radar.continuousMode"
                type="checkbox"
              />
              <span class="checkmark"></span>
              Continuous Scan Mode
            </label>
          </div>
        </div>
      </div>

      <!-- Stepper Motor Settings -->
      <div class="card stepper-settings">
        <h2>Stepper Motor Settings</h2>
        <div class="setting-group">
          <div class="setting-item">
            <label for="defaultSpeed">Default Speed (RPM):</label>
            <input
              id="defaultSpeed"
              v-model.number="localSettings.stepper.defaultSpeed"
              type="number"
              min="1"
              max="100"
            />
          </div>
          <div class="setting-item">
            <label for="acceleration">Acceleration:</label>
            <input
              id="acceleration"
              v-model.number="localSettings.stepper.acceleration"
              type="number"
              min="1"
              max="1000"
            />
          </div>
          <div class="setting-item">
            <label for="homePosition">Home Position (degrees):</label>
            <input
              id="homePosition"
              v-model.number="localSettings.stepper.homePosition"
              type="number"
              min="0"
              max="360"
            />
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input
                v-model="localSettings.stepper.enableLimits"
                type="checkbox"
              />
              <span class="checkmark"></span>
              Enable Position Limits
            </label>
          </div>
        </div>
      </div>

      <!-- Display Settings -->
      <div class="card display-settings">
        <h2>Display Settings</h2>
        <div class="setting-group">
          <div class="setting-item">
            <label for="theme">Theme:</label>
            <select id="theme" v-model="localSettings.display.theme">
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto</option>
            </select>
          </div>
          <div class="setting-item">
            <label for="updateInterval">Update Interval (ms):</label>
            <input
              id="updateInterval"
              v-model.number="localSettings.display.updateInterval"
              type="number"
              min="100"
              max="5000"
              step="100"
            />
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input
                v-model="localSettings.display.showGrid"
                type="checkbox"
              />
              <span class="checkmark"></span>
              Show Grid on Radar Display
            </label>
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input
                v-model="localSettings.display.enableAnimations"
                type="checkbox"
              />
              <span class="checkmark"></span>
              Enable Animations
            </label>
          </div>
        </div>
      </div>

      <!-- Notification Settings -->
      <div class="card notification-settings">
        <h2>Notification Settings</h2>
        <div class="setting-group">
          <div class="setting-item">
            <label class="checkbox-label">
              <input
                v-model="localSettings.notifications.enableSound"
                type="checkbox"
              />
              <span class="checkmark"></span>
              Enable Sound Notifications
            </label>
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input
                v-model="localSettings.notifications.enableDesktop"
                type="checkbox"
              />
              <span class="checkmark"></span>
              Enable Desktop Notifications
            </label>
          </div>
          <div class="setting-item">
            <label for="notificationDuration">Notification Duration (ms):</label>
            <input
              id="notificationDuration"
              v-model.number="localSettings.notifications.duration"
              type="number"
              min="1000"
              max="10000"
              step="500"
            />
          </div>
        </div>
      </div>

      <!-- System Settings -->
      <div class="card system-settings">
        <h2>System Settings</h2>
        <div class="setting-group">
          <div class="setting-item">
            <label for="logLevel">Log Level:</label>
            <select id="logLevel" v-model="localSettings.system.logLevel">
              <option value="error">Error</option>
              <option value="warn">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>
          <div class="setting-item">
            <label for="maxLogEntries">Max Log Entries:</label>
            <input
              id="maxLogEntries"
              v-model.number="localSettings.system.maxLogEntries"
              type="number"
              min="10"
              max="1000"
            />
          </div>
          <div class="setting-item">
            <label class="checkbox-label">
              <input
                v-model="localSettings.system.enableDebugMode"
                type="checkbox"
              />
              <span class="checkmark"></span>
              Enable Debug Mode
            </label>
          </div>
        </div>
    </div>

    <div class="settings-actions">
      <button @click="saveSettings" class="btn btn-primary">
        Save Settings
      </button>
      <button @click="cancelChanges" class="btn btn-secondary">
        Cancel
      </button>
      <button @click="exportSettings" class="btn btn-outline">
        Export Settings
      </button>
      <button @click="importSettings" class="btn btn-outline">
        Import Settings
      </button>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import apiService from '@/services/apiService'

export default {
  name: 'Settings',

  data() {
    return {
      localSettings: {
        serverUrl: 'http://localhost:3001',
        websocketUrl: 'ws://localhost:3001',
        reconnectInterval: 5000,
        autoReconnect: true,
        radar: {
          detectionRange: 100,
          sensitivity: 5,
          scanSpeed: 'medium',
          continuousMode: false
        },
        stepper: {
          defaultSpeed: 50,
          acceleration: 100,
          homePosition: 0,
          enableLimits: true
        },
        display: {
          theme: 'light',
          updateInterval: 1000,
          showGrid: true,
          enableAnimations: true
        },
        notifications: {
          enableSound: true,
          enableDesktop: false,
          duration: 3000
        },
        system: {
          logLevel: 'info',
          maxLogEntries: 100,
          enableDebugMode: false
        }
      }
    }
  },

  computed: {
    ...mapGetters('system', ['systemSettings']),

    allConnected() {
      return this.$store.getters['connection/allConnected']
    }
  },

  mounted() {
    // Load current settings
    if (this.systemSettings) {
      this.localSettings = { ...this.systemSettings }
    }
    // Load microcontroller settings from server
    this.loadMicrocontrollerSettings()
  },

  methods: {
    ...mapActions('system', ['updateSettings']),
    ...mapActions('notifications', ['showNotification']),

    saveSettings() {
      this.updateSettings(this.localSettings)
      this.showNotification({
        message: 'Settings saved successfully',
        type: 'success'
      })
    },

    cancelChanges() {
      // Reset to original settings
      if (this.systemSettings) {
        this.localSettings = { ...this.systemSettings }
      }
      this.showNotification({
        message: 'Changes cancelled',
        type: 'info'
      })
    },

    resetToDefaults() {
      if (confirm('Are you sure you want to reset all settings to defaults?')) {
        // Reset to default values
        this.localSettings = {
          serverUrl: 'http://localhost:3001',
          websocketUrl: 'ws://localhost:3001',
          reconnectInterval: 5000,
          autoReconnect: true,
          radar: {
            detectionRange: 100,
            sensitivity: 5,
            scanSpeed: 'medium',
            continuousMode: false
          },
          stepper: {
            defaultSpeed: 50,
            acceleration: 100,
            homePosition: 0,
            enableLimits: true
          },
          display: {
            theme: 'light',
            updateInterval: 1000,
            showGrid: true,
            enableAnimations: true
          },
          notifications: {
            enableSound: true,
            enableDesktop: false,
            duration: 3000
          },
          system: {
            logLevel: 'info',
            maxLogEntries: 100,
            enableDebugMode: false
          }
        }

        this.showNotification({
          message: 'Settings reset to defaults',
          type: 'info'
        })
      }
    },

    exportSettings() {
      const dataStr = JSON.stringify(this.localSettings, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)

      const link = document.createElement('a')
      link.href = url
      link.download = 'radar-settings.json'
      link.click()

      URL.revokeObjectURL(url)

      this.showNotification({
        message: 'Settings exported successfully',
        type: 'success'
      })
    },

    importSettings() {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'

      input.onchange = (event) => {
        const file = event.target.files[0]
        if (file) {
          const reader = new FileReader()
          reader.onload = (e) => {
            try {
              const settings = JSON.parse(e.target.result)
              this.localSettings = { ...settings }
              this.showNotification({
                message: 'Settings imported successfully',
                type: 'success'
              })
            } catch (error) {
              this.showNotification({
                message: 'Failed to import settings: Invalid file format',
                type: 'error'
              })
            }
          }
          reader.readAsText(file)
        }
      }

      input.click()
    },

    async loadMicrocontrollerSettings() {
      try {
        const response = await apiService.get('/api/config/microcontroller-settings')
        if (response.data.success && response.data.settings) {
          const settings = response.data.settings
          // Merge loaded settings into local settings
          if (settings.radar) {
            Object.assign(this.localSettings.radar, settings.radar)
          }
          if (settings.stepper) {
            Object.assign(this.localSettings.stepper, settings.stepper)
          }
          this.showNotification({
            message: 'Microcontroller settings loaded from server',
            type: 'info'
          })
        }
      } catch (error) {
        console.error('Error loading microcontroller settings:', error)
        // Silently fail - use local defaults if server settings unavailable
      }
    }
  }
}
</script>

<style scoped>
.settings {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  color: #333;
}

.settings-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.setting-item label {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.setting-item input[type="text"],
.setting-item input[type="url"],
.setting-item input[type="number"],
.setting-item select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.setting-item input[type="range"] {
  width: 100%;
}

.range-value {
  align-self: flex-end;
  font-weight: 500;
  color: #666;
  font-size: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  font-weight: normal !important;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
}

.checkmark {
  font-size: 14px;
}

.settings-actions {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  padding: 20px 0;
  border-top: 1px solid #eee;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: background-color 0.2s;
}

.btn-primary {
  background: #2196f3;
  color: white;
}

.btn-primary:hover {
  background: #1976d2;
}

.btn-secondary {
  background: #666;
  color: white;
}

.btn-secondary:hover {
  background: #555;
}

.btn-outline {
  background: transparent;
  color: #2196f3;
  border: 1px solid #2196f3;
}

.btn-outline:hover {
  background: #f5f5f5;
}

/* Responsive design */
@media (max-width: 768px) {
  .settings-sections {
    grid-template-columns: 1fr;
  }

  .settings-actions {
    flex-direction: column;
  }

  .page-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
  }
}

.button-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.button-group .btn {
  flex: 1;
  min-width: 120px;
}

.servo-settings .badge {
  padding: 6px 12px;
  font-size: 14px;
}

.alert {
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 15px;
  border: 1px solid #ffc107;
  background: #fff3cd;
  color: #856404;
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #45a049;
}

.btn-warning {
  background: #ff9800;
  color: white;
}

.btn-warning:hover:not(:disabled) {
  background: #e68900;
}

.btn-outline-info {
  border: 1px solid #2196f3;
  background: transparent;
  color: #2196f3;
}

.btn-outline-info:hover:not(:disabled) {
  background: #2196f3;
  color: white;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
