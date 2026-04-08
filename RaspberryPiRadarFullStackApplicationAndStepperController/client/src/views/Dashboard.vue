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
            <span class="connection-name">Pico Connection:</span>
            <span class="connection-status" :class="{ connected: picoConnected }">
              {{ picoConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>
          <div class="connection-item">
            <span class="connection-name">WebSocket:</span>
            <span class="connection-status" :class="{ connected: socketConnected }">
              {{ socketConnected ? 'Connected' : 'Disconnected' }}
            </span>
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
      'picoConnected',
      'socketConnected'
    ]),

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

.connection-status {
  padding: 4px 8px;
  border-radius: 4px;
  background: #f44336;
  color: white;
  font-size: 12px;
}

.connection-status.connected {
  background: #4caf50;
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
</style>
