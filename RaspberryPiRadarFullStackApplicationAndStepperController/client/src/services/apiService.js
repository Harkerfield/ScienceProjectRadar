import axios from 'axios'

// Determine API base URL intelligently
function getApiBaseUrl() {
  // Check if explicitly set in environment
  if (process.env.VUE_APP_API_BASE_URL) {
    return process.env.VUE_APP_API_BASE_URL
  }
  
  // Auto-detect based on current location
  const protocol = window.location.protocol
  const hostname = window.location.hostname
  const port = window.location.port || (protocol === 'https:' ? 443 : 80)
  
  // If we're accessing via .local hostname, assume API is on same host
  if (hostname.includes('.local') || hostname === 'localhost' || hostname === '127.0.0.1') {
    return `${protocol}//${hostname}${port ? ':' + port : ''}/api`
  }
  
  // Default fallback
  return `${protocol}//${hostname}:3000/api`
}

// Create axios instance with default configuration
const apiService = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
apiService.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Log requests in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`, config.data)
    }

    return config
  },
  (error) => {
    console.error('API Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
apiService.interceptors.response.use(
  (response) => {
    // Log responses in development
    if (process.env.NODE_ENV === 'development') {
      console.log(`API Response: ${response.status} ${response.config.url}`, response.data)
    }

    return response
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data || error.message)

    // Handle specific error cases
    if (error.response?.status === 401) {
      // Unauthorized - clear auth and redirect to login
      localStorage.removeItem('authToken')
      // Could dispatch a logout action here
    }

    if (error.response?.status >= 500) {
      // Server error - could show a global notification
      console.error('Server error occurred')
    }

    return Promise.reject(error)
  }
)

export default apiService
