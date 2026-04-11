import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import socketService from './services/socketService'

// Import CSS frameworks (all bundled locally, no CDN)
import 'bootstrap/dist/css/bootstrap.min.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

// Import Bootstrap JS functionality
import 'bootstrap'

// Import global styles
import './assets/css/main.css'

const app = createApp(App)

// Initialize socket service with store
socketService.init(store)

// Load persisted data
store.dispatch('radar/loadPersistedData')

// Connect to server when app starts
socketService.connect()
  .then(() => {
    console.log('Connected to server')
  })
  .catch((error) => {
    console.warn('Failed to connect to server:', error)
  })

// Periodic maintenance tasks
setInterval(() => {
  if (store.hasModule && store.hasModule('pico')) {
    store.dispatch('pico/performMaintenance')
  }
}, 10 * 60 * 1000) // Every 10 minutes

app.use(store)
app.use(router)

// Global error handler
app.config.errorHandler = (err, instance, info) => {
  console.error('Global error:', err)
  console.error('Component info:', info)

  // You could send this to a logging service
  store.dispatch('notifications/addNotification', {
    type: 'error',
    title: 'Application Error',
    message: err.message || 'An unexpected error occurred'
  })
}

app.mount('#app')
