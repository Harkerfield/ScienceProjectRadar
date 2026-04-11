<template>
  <div id="app">
    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
      <div class="container-fluid">
        <router-link class="navbar-brand" to="/">
          <i class="fas fa-radar-dish me-2"></i>
          Radar Control System
        </router-link>

        <button
          class="navbar-toggler"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto">
            <li class="nav-item">
              <router-link class="nav-link" to="/" active-class="active">
                <i class="fas fa-tachometer-alt me-1"></i>
                Dashboard
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/stepper" active-class="active">
                <i class="fas fa-cog me-1"></i>
                Stepper Control
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/radar" active-class="active">
                <i class="fas fa-satellite-dish me-1"></i>
                Radar Control
              </router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" to="/settings" active-class="active">
                <i class="fas fa-sliders-h me-1"></i>
                Settings
              </router-link>
            </li>
          </ul>

          <!-- Connection Status -->
          <div class="navbar-text me-3">
            <span
              :class="[
                'status-indicator',
                connectionStatus === 'connected' ? 'status-online' :
                connectionStatus === 'connecting' ? 'status-connecting' : 'status-offline'
              ]"
            ></span>
            {{ connectionStatusText }}
          </div>

          <!-- System Status -->
          <div class="navbar-text">
            <span class="badge bg-secondary">
              <i class="fas fa-server me-1"></i>
              {{ systemStatus }}
            </span>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="container-fluid mt-3">
      <router-view />
    </main>

    <!-- Notifications -->
    <NotificationContainer />

    <!-- Loading Overlay -->
    <div v-if="isLoading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p class="mt-3">{{ loadingMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex'
import NotificationContainer from './components/NotificationContainer.vue'
import socketService from './services/socketService'

export default {
  name: 'App',
  components: {
    NotificationContainer
  },

  computed: {
    ...mapState(['isLoading', 'loadingMessage']),
    ...mapState('connection', ['connectionStatus']),
    ...mapGetters('connection', ['connectionStatusText']),
    ...mapGetters('system', ['systemStatus'])
  },

  async created() {
    // Initialize the application
    await this.initializeApp()
  },

  beforeUnmount() {
    // Cleanup socket connection
    socketService.disconnect()
  },

  methods: {
    ...mapActions(['setLoading']),
    ...mapActions('connection', ['initializeConnection']),
    ...mapActions('notifications', ['addNotification']),

    async initializeApp() {
      try {
        this.setLoading({ isLoading: true, message: 'Initializing application...' })

        // Initialize socket connection
        await this.initializeConnection()

        // Load initial data
        await this.loadInitialData()

        this.addNotification({
          type: 'success',
          title: 'Connected',
          message: 'Successfully connected to radar control system'
        })
      } catch (error) {
        console.error('Failed to initialize app:', error)
        this.addNotification({
          type: 'error',
          title: 'Connection Failed',
          message: 'Failed to connect to the server. Please check your connection.'
        })
      } finally {
        this.setLoading({ isLoading: false })
      }
    },

    async loadInitialData() {
      // Load system status and initial state
      await Promise.all([
        this.$store.dispatch('stepper/fetchStatus'),
        this.$store.dispatch('radar/fetchStatus'),
        this.$store.dispatch('system/fetchStatus')
      ])
    }
  }
}
</script>

<style scoped>
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.loading-content {
  text-align: center;
  color: white;
}

.nav-link.active {
  background-color: rgba(255, 255, 255, 0.1) !important;
  border-radius: 6px;
}
</style>
