// Determine API base URL intelligently
function getApiBaseUrl() {
  // Check if explicitly set in environment
  if (process.env.VUE_APP_API_BASE_URL) {
    return process.env.VUE_APP_API_BASE_URL
  }

  // Auto-detect based on current location
  // Always use HTTP for local network access
  const hostname = window.location.hostname
  const port = window.location.port || 3000

  // Always use HTTP for local network access
  return `http://${hostname}:${port}/api`
}

function buildHeaders(customHeaders = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders
  }

  const token = localStorage.getItem('authToken')
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  return headers
}

async function request(method, url, data = undefined, config = {}) {
  const baseURL = getApiBaseUrl()
  const fullUrl = `${baseURL}${url}`
  const controller = new AbortController()
  const timeoutMs = config.timeout || 10000
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  const options = {
    method,
    headers: buildHeaders(config.headers),
    signal: controller.signal
  }

  if (typeof data !== 'undefined') {
    options.body = JSON.stringify(data)
  }

  if (process.env.NODE_ENV === 'development') {
    console.log(`API Request: ${method.toUpperCase()} ${url}`, data)
  }

  try {
    const response = await fetch(fullUrl, options)

    let responseData = null
    const contentType = response.headers.get('content-type') || ''

    if (contentType.includes('application/json')) {
      responseData = await response.json()
    } else {
      const text = await response.text()
      responseData = text ? { message: text } : null
    }

    const result = {
      data: responseData,
      status: response.status,
      ok: response.ok,
      headers: response.headers,
      config: { method, url }
    }

    if (process.env.NODE_ENV === 'development') {
      console.log(`API Response: ${response.status} ${url}`, responseData)
    }

    if (!response.ok) {
      const error = new Error(responseData?.error || response.statusText || 'Request failed')
      error.response = result
      throw error
    }

    return result
  } catch (error) {
    const status = error.response?.status
    const dataFromError = error.response?.data

    console.error('API Response Error:', status, dataFromError || error.message)

    // Handle specific error cases
    if (status === 401) {
      localStorage.removeItem('authToken')
    }

    if (status >= 500) {
      console.error('Server error occurred')
    }

    if (error.name === 'AbortError') {
      const timeoutError = new Error(`Request timed out after ${timeoutMs}ms`)
      timeoutError.response = {
        status: 408,
        data: { error: timeoutError.message },
        ok: false
      }
      throw timeoutError
    }

    throw error
  } finally {
    clearTimeout(timeoutId)
  }
}

const apiService = {
  get(url, config = {}) {
    return request('GET', url, undefined, config)
  },

  post(url, data = {}, config = {}) {
    return request('POST', url, data, config)
  },

  put(url, data = {}, config = {}) {
    return request('PUT', url, data, config)
  },

  patch(url, data = {}, config = {}) {
    return request('PATCH', url, data, config)
  },

  delete(url, config = {}) {
    return request('DELETE', url, undefined, config)
  }
}

export default apiService
