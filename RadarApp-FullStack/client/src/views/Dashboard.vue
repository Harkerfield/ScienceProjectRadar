<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1>System Dashboard</h1>
      <div class="system-status">
        <span class="status-indicator" :class="systemStatusClass"></span>
        <span class="status-text">{{ systemStatus }}</span>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- System Overview -->
      <div class="card system-overview">
        <h2>System Overview</h2>
        <div class="stats">
          <div class="stat">
            <span class="label">Uptime:</span>
            <span class="value">{{ formatUptime(uptime) }}</span>
          </div>
          <div class="stat">
            <span class="label">Status:</span>
            <span class="value">{{ systemStatus }}</span>
          </div>
          <div class="stat">
            <span class="label">Last Heartbeat:</span>
            <span class="value">{{ formatTime(lastHeartbeat) }}</span>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card quick-actions">
        <h2>Quick Actions</h2>
        <div class="action-buttons">
          <router-link to="/radar" class="action-btn radar">
            <i class="icon-radar"></i>
            <span>Radar Control</span>
          </router-link>
          <router-link to="/stepper" class="action-btn stepper">
            <i class="icon-stepper"></i>
            <span>Stepper Control</span>
          </router-link>
          <router-link to="/settings" class="action-btn settings">
            <i class="icon-settings"></i>
            <span>Settings</span>
          </router-link>
        </div>
      </div>

      <!-- Connection Status -->
      <div class="card connection-status">
        <h2>Connection Status</h2>
        <div class="connections">
          <div class="connection-item">
            <span class="connection-name">Server (WebSocket):</span>
            <span class="connection-badge" :class="{ connected: websocketConnected }">
              <span class="status-dot" :class="{ connected: websocketConnected }"></span>
              {{ websocketConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="connection-item">
            <span class="connection-name">Serial Bridge:</span>
            <span class="connection-badge" :class="{ connected: serialConnected }">
              <span class="status-dot" :class="{ connected: serialConnected }"></span>
              {{ serialConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="connection-item">
            <span class="connection-name">Pico Master (UART):</span>
            <span class="connection-badge" :class="{ connected: picoConnected }">
              <span class="status-dot" :class="{ connected: picoConnected }"></span>
              {{ picoConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="connection-item">
            <span class="connection-name">Overall Status:</span>
            <span class="connection-text" :class="{ warning: !allConnected }">{{ overallStatus }}</span>
          </div>
          <div v-if="!allConnected" class="connection-warning">
            ⚠️ Devices disabled until all connections are established
          </div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="card recent-activity">
        <h2>Recent Activity</h2>
        <div class="activity-list">
          <div v-if="recentErrors.length > 0" class="activity-section">
            <h3>Recent Errors</h3>
            <ul class="error-list">
              <li v-for="error in recentErrors" :key="error.id" class="error-item">
                <span class="error-time">{{ formatTime(error.timestamp) }}</span>
                <span class="error-message">{{ error.message }}</span>
              </li>
            </ul>
          </div>
          <div v-else class="no-activity">
            <p>No recent errors</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  name: 'Dashboard',

  computed: {
    ...mapGetters('system', [
      'systemStatus',
      'uptime',
      'lastHeartbeat',
      'errorLogs',
      'isOnline'
    ]),
    ...mapGetters('connection', [
      'isConnected',
      'connectionStatusText',
      'websocketStatusText',
      'picoStatusText'
    ]),

    websocketConnected() {
      return this.$store.state.connection.websocketStatus === 'connected'
    },

    serialConnected() {
      return this.$store.state.connection.serialConnected
    },

    picoConnected() {
      return this.$store.state.connection.picoConnected
    },

    allConnected() {
      return this.websocketConnected && this.serialConnected && this.picoConnected
    },

    overallStatus() {
      if (this.allConnected) {
        return 'All systems operational - Ready for control'
      } else {
        const statuses = []
        if (!this.websocketConnected) statuses.push('Server')
        if (!this.serialConnected) statuses.push('Serial')
        if (!this.picoConnected) statuses.push('Pico')
        return `Waiting for: ${statuses.join(', ')}`
      }
    },

    systemStatusClass() {
      return {
        'status-online': this.systemStatus === 'running',
        'status-offline': this.systemStatus === 'offline',
        'status-error': this.systemStatus === 'error'
      }
    },

    recentErrors() {
      return this.errorLogs.slice(0, 5)
    }
  },

  methods: {
    formatUptime(seconds) {
      if (!seconds) return '00:00:00'

      const hours = Math.floor(seconds / 3600)
      const minutes = Math.floor((seconds % 3600) / 60)
      const secs = seconds % 60

      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    },

    formatTime(timestamp) {
      if (!timestamp) return 'Never'

      const date = new Date(timestamp)
      return date.toLocaleTimeString()
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.dashboard-header h1 {
  margin: 0;
  color: #333;
}

.system-status {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #ccc;
}

.status-indicator.status-online {
  background-color: #4caf50;
}

.status-indicator.status-offline {
  background-color: #f44336;
}

.status-indicator.status-error {
  background-color: #ff9800;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 18px;
}

.stats {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat {
  display: flex;
  justify-content: space-between;
}

.stat .label {
  font-weight: 500;
  color: #666;
}

.stat .value {
  color: #333;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 6px;
  text-decoration: none;
  color: #333;
  transition: background-color 0.2s;
}

.action-btn:hover {
  background: #e0e0e0;
}

.connections {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.connection-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.connection-name {
  font-weight: 500;
  color: #333;
  min-width: 180px;
}

.connection-text {
  color: #333;
  font-size: 14px;
  font-weight: 500;
}

.connection-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 4px;
  background: #f44336;
  color: white;
  font-size: 12px;
}

.connection-badge.connected {
  background: #4caf50;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #ccc;
  display: inline-block;
}

.status-dot.connected {
  background-color: #fff;
  box-shadow: inset 0 0 2px rgba(0, 0, 0, 0.2);
}

.error-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.error-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: #ffebee;
  border-radius: 4px;
  margin-bottom: 8px;
}

.error-time {
  font-size: 12px;
  color: #666;
}

.error-message {
  font-size: 14px;
  color: #d32f2f;
}

.no-activity {
  text-align: center;
  color: #666;
  font-style: italic;
}

.connection-warning {
  margin-top: 12px;
  padding: 10px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  color: #856404;
  font-size: 13px;
  font-weight: 500;
  text-align: center;
}

.connection-text.warning {
  color: #ff9800;
  font-weight: bold;
}
</style>
