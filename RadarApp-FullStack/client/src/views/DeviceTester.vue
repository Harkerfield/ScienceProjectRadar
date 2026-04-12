<template>
  <div class="device-tester">
    <div class="page-header">
      <h1>
        <i class="fas fa-microchip me-2"></i>
        Microcontroller Tester
      </h1>
      <span class="connection-status" :class="{ connected: allConnected }">
        {{ allConnected ? '✓ Connected' : '✗ Disconnected' }}
      </span>
    </div>

    <div class="tester-container">
      <!-- Command Builder -->
      <div class="card command-builder">
        <h2>Command Builder</h2>

        <div v-if="!allConnected" class="alert alert-warning">
          ⚠️ All connections required to send commands (Server, Serial, Pico)
        </div>

        <div class="form-group">
          <label for="device-select">Device:</label>
          <select
            id="device-select"
            v-model="selectedDevice"
            @change="updateAvailableCommands"
            :disabled="!allConnected"
          >
            <option value="">-- Select Device --</option>
            <option value="MASTER">MASTER</option>
            <option value="STEPPER">STEPPER</option>
            <option value="SERVO">SERVO</option>
            <option value="RADAR">RADAR</option>
          </select>
        </div>

        <div class="form-group">
          <label for="command-select">Command:</label>
          <select
            id="command-select"
            v-model="selectedCommand"
            @change="updateCommandParams"
            :disabled="!selectedDevice || !allConnected"
          >
            <option value="">-- Select Command --</option>
            <option
              v-for="cmd in availableCommands"
              :key="cmd"
              :value="cmd"
            >
              {{ cmd }}
            </option>
          </select>
        </div>

        <div v-if="selectedCommand && requiredParams.length > 0" class="params-section">
          <h4>Parameters:</h4>
          <div
            v-for="param in requiredParams"
            :key="param"
            class="form-group"
          >
            <label :for="`param-${param}`">{{ param }}:</label>
            <input
              :id="`param-${param}`"
              v-model="commandParams[param]"
              type="text"
              :placeholder="`Enter ${param}`"
            />
          </div>
        </div>

        <div class="form-actions">
          <button
            @click="sendCommand"
            :disabled="!selectedDevice || !selectedCommand || !allConnected || isSending"
            class="btn btn-primary btn-lg"
          >
            <i :class="['fas', isSending ? 'fa-spinner fa-spin' : 'fa-paper-plane', 'me-2']"></i>
            {{ isSending ? 'Sending...' : 'Send Command' }}
          </button>
          <button
            @click="resetForm"
            :disabled="!selectedDevice"
            class="btn btn-secondary btn-lg"
          >
            <i class="fas fa-redo me-2"></i>
            Reset
          </button>
        </div>
      </div>

      <!-- Command History & Response -->
      <div class="history-response">
        <!-- Current Response -->
        <div class="card response-panel">
          <h2>Response</h2>
          <div v-if="lastResponse" class="response-content">
            <div :class="['response-status', lastResponse.success ? 'success' : 'error']">
              {{ lastResponse.success ? '✓ Success' : '✗ Error' }}
            </div>
            <pre class="response-json">{{ JSON.stringify(lastResponse.data, null, 2) }}</pre>
          </div>
          <div v-else class="empty-state">
            Send a command to see the response
          </div>
        </div>

        <!-- Command History -->
        <div class="card history-panel">
          <h2>History</h2>
          <div v-if="commandHistory.length > 0" class="history-list">
            <div
              v-for="(item, index) in commandHistory"
              :key="index"
              class="history-item"
              :class="{ 'active': index === selectedHistoryIndex }"
              @click="selectHistoryItem(index)"
            >
              <div class="history-command">
                <strong>{{ item.device }}:{{ item.command }}</strong>
              </div>
              <div class="history-time">
                {{ formatTime(item.timestamp) }}
              </div>
              <div :class="['history-status', item.success ? 'success' : 'error']">
                {{ item.success ? 'OK' : 'ERR' }}
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            No commands sent yet
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import apiService from '../services/apiService'

export default {
  name: 'DeviceTester',

  data() {
    return {
      selectedDevice: '',
      selectedCommand: '',
      commandParams: {},
      availableCommands: [],
      requiredParams: [],
      lastResponse: null,
      commandHistory: [],
      selectedHistoryIndex: -1,
      isSending: false,
      deviceCommands: {
        MASTER: ['PING', 'STATUS', 'WHOAMI'],
        STEPPER: ['PING', 'STATUS', 'WHOAMI', 'SPEED', 'SPIN', 'STOP', 'MOVE', 'HOME', 'ENABLE', 'DISABLE', 'ROTATE'],
        SERVO: ['PING', 'STATUS', 'WHOAMI', 'OPEN', 'CLOSE'],
        RADAR: ['PING', 'STATUS', 'WHOAMI', 'READ', 'SET_RANGE', 'SET_VELOCITY']
      },
      commandParams: {
        SPEED: { speed_us: '' },
        SPIN: { speed: '' },
        MOVE: { degrees: '' },
        ROTATE: { speed: '' },
        SET_RANGE: { centimeters: '' },
        SET_VELOCITY: { meters_per_second: '' }
      }
    }
  },

  computed: {
    ...mapState('connection', ['serialConnected', 'picoConnected', 'websocketStatus']),

    allConnected() {
      return this.$store.getters['connection/allConnected']
    }
  },

  methods: {
    updateAvailableCommands() {
      if (this.selectedDevice) {
        this.availableCommands = this.deviceCommands[this.selectedDevice] || []
        this.selectedCommand = ''
        this.requiredParams = []
        this.commandParams = {}
      } else {
        this.availableCommands = []
      }
    },

    updateCommandParams() {
      if (this.selectedCommand && this.commandParams[this.selectedCommand]) {
        this.requiredParams = Object.keys(this.commandParams[this.selectedCommand])
        this.commandParams = { ...this.commandParams[this.selectedCommand] }
      } else {
        this.requiredParams = []
        this.commandParams = {}
      }
    },

    async sendCommand() {
      if (!this.selectedDevice || !this.selectedCommand || !this.allConnected) {
        return
      }

      this.isSending = true

      try {
        const endpoint = `/api/device/${this.selectedDevice}/${this.selectedCommand}`
        const body = {
          args: this.commandParams
        }

        const response = await apiService.post(endpoint, body)

        const historyItem = {
          device: this.selectedDevice,
          command: this.selectedCommand,
          params: { ...this.commandParams },
          timestamp: new Date(),
          success: response.data.success !== false,
          data: response.data
        }

        this.commandHistory.unshift(historyItem)
        if (this.commandHistory.length > 50) {
          this.commandHistory.pop()
        }

        this.lastResponse = {
          success: response.data.success !== false,
          data: response.data
        }

        this.$store.dispatch('notifications/showSuccess', 'Command sent successfully')
      } catch (error) {
        const historyItem = {
          device: this.selectedDevice,
          command: this.selectedCommand,
          params: { ...this.commandParams },
          timestamp: new Date(),
          success: false,
          data: {
            error: error.message,
            response: error.response?.data
          }
        }

        this.commandHistory.unshift(historyItem)
        if (this.commandHistory.length > 50) {
          this.commandHistory.pop()
        }

        this.lastResponse = {
          success: false,
          data: historyItem.data
        }

        this.$store.dispatch('notifications/showError', `Command failed: ${error.message}`)
      } finally {
        this.isSending = false
      }
    },

    selectHistoryItem(index) {
      this.selectedHistoryIndex = index
      const item = this.commandHistory[index]
      this.lastResponse = {
        success: item.success,
        data: item.data
      }
    },

    resetForm() {
      this.selectedDevice = ''
      this.selectedCommand = ''
      this.commandParams = {}
      this.availableCommands = []
      this.requiredParams = []
      this.updateAvailableCommands()
    },

    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${hours}:${minutes}:${seconds}`
    }
  }
}
</script>

<style scoped>
.device-tester {
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
  font-size: 28px;
}

.connection-status {
  padding: 8px 16px;
  border-radius: 20px;
  background: #f5f5f5;
  color: #666;
  font-weight: 500;
  font-size: 14px;
}

.connection-status.connected {
  background: #4caf50;
  color: white;
}

.tester-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
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

.card h4 {
  margin: 15px 0 10px 0;
  color: #666;
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

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #333;
  font-weight: 500;
  font-size: 14px;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  font-family: monospace;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #2196f3;
  box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
}

.form-group select:disabled,
.form-group input:disabled {
  background: #f5f5f5;
  color: #999;
  cursor: not-allowed;
}

.params-section {
  background: #f9f9f9;
  padding: 15px;
  border-radius: 4px;
  margin: 15px 0;
  border-left: 3px solid #2196f3;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-primary {
  background: #2196f3;
  color: white;
  flex: 1;
}

.btn-primary:hover:not(:disabled) {
  background: #1976d2;
}

.btn-secondary {
  background: #666;
  color: white;
  flex: 1;
}

.btn-secondary:hover:not(:disabled) {
  background: #555;
}

.btn-lg {
  padding: 14px 24px;
  font-size: 16px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.history-response {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.response-panel,
.history-panel {
  grid-column: span 1;
}

.response-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.response-status {
  padding: 12px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 14px;
  text-align: center;
}

.response-status.success {
  background: #4caf50;
  color: white;
}

.response-status.error {
  background: #f44336;
  color: white;
}

.response-json {
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 12px;
  font-family: monospace;
  font-size: 12px;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  color: #333;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 30px 20px;
  font-style: italic;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 500px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background: #f0f0f0;
  border-color: #2196f3;
}

.history-item.active {
  background: #e3f2fd;
  border-color: #2196f3;
  font-weight: 600;
}

.history-command {
  flex: 1;
  font-family: monospace;
  font-size: 13px;
  color: #333;
}

.history-time {
  color: #999;
  font-size: 12px;
  margin: 0 15px;
}

.history-status {
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
  min-width: 40px;
  text-align: center;
}

.history-status.success {
  background: #4caf50;
  color: white;
}

.history-status.error {
  background: #f44336;
  color: white;
}

.command-builder {
  grid-column: span 1;
}

@media (max-width: 1200px) {
  .tester-container {
    grid-template-columns: 1fr;
  }

  .command-builder {
    grid-column: span 1;
  }

  .history-response {
    grid-template-columns: 1fr;
  }

  .response-panel,
  .history-panel {
    grid-column: span 1;
  }
}
</style>
