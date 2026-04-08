<template>
  <div class="not-found">
    <div class="error-content">
      <div class="error-icon">
        <svg viewBox="0 0 24 24" width="120" height="120">
          <path fill="#ccc" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20C7.59,20 4,16.41 4,12C7.59,4 12,4Z M15.5,17L9,10.5L10.5,9L17,15.5L15.5,17Z"/>
        </svg>
      </div>

      <h1 class="error-title">404</h1>
      <h2 class="error-subtitle">Page Not Found</h2>

      <p class="error-message">
        The page you're looking for doesn't exist or has been moved.
      </p>

      <div class="error-actions">
        <router-link to="/" class="btn btn-primary">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M10,20V14H14V20H19V12H22L12,3L2,12H5V20H10Z"/>
          </svg>
          Go Home
        </router-link>

        <button @click="goBack" class="btn btn-secondary">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="currentColor" d="M20,11V13H8L13.5,18.5L12.08,19.92L4.16,12L12.08,4.08L13.5,5.5L8,11H20Z"/>
          </svg>
          Go Back
        </button>
      </div>

      <div class="help-section">
        <h3>Quick Navigation</h3>
        <div class="quick-links">
          <router-link to="/" class="quick-link">
            <div class="link-icon">📊</div>
            <div class="link-content">
              <div class="link-title">Dashboard</div>
              <div class="link-desc">System overview and status</div>
            </div>
          </router-link>

          <router-link to="/radar" class="quick-link">
            <div class="link-icon">📡</div>
            <div class="link-content">
              <div class="link-title">Radar Control</div>
              <div class="link-desc">Radar monitoring and control</div>
            </div>
          </router-link>

          <router-link to="/stepper" class="quick-link">
            <div class="link-icon">⚙️</div>
            <div class="link-content">
              <div class="link-title">Stepper Control</div>
              <div class="link-desc">Motor position and movement</div>
            </div>
          </router-link>

          <router-link to="/settings" class="quick-link">
            <div class="link-icon">⚙️</div>
            <div class="link-content">
              <div class="link-title">Settings</div>
              <div class="link-desc">System configuration</div>
            </div>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotFound',

  methods: {
    goBack() {
      // Check if there's history to go back to
      if (window.history.length > 1) {
        this.$router.go(-1)
      } else {
        // If no history, go to home
        this.$router.push('/')
      }
    }
  },

  mounted() {
    // Update document title
    document.title = 'Page Not Found - Radar Control System'
  }
}
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.error-content {
  text-align: center;
  max-width: 600px;
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.error-icon {
  margin-bottom: 30px;
}

.error-icon svg {
  opacity: 0.7;
}

.error-title {
  font-size: 4rem;
  font-weight: 700;
  color: #333;
  margin: 0 0 10px 0;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

.error-subtitle {
  font-size: 1.5rem;
  color: #666;
  margin: 0 0 20px 0;
  font-weight: 400;
}

.error-message {
  font-size: 1rem;
  color: #777;
  margin-bottom: 30px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary {
  background: #2196f3;
  color: white;
}

.btn-primary:hover {
  background: #1976d2;
  transform: translateY(-2px);
}

.btn-secondary {
  background: #666;
  color: white;
}

.btn-secondary:hover {
  background: #555;
  transform: translateY(-2px);
}

.help-section {
  border-top: 1px solid #eee;
  padding-top: 30px;
}

.help-section h3 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 1.2rem;
}

.quick-links {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.quick-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  text-decoration: none;
  color: #333;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.quick-link:hover {
  background: #e3f2fd;
  border-color: #2196f3;
  transform: translateY(-2px);
}

.link-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.link-content {
  flex: 1;
  text-align: left;
}

.link-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 2px;
}

.link-desc {
  font-size: 12px;
  color: #666;
}

/* Responsive design */
@media (max-width: 768px) {
  .error-content {
    padding: 30px 20px;
  }

  .error-title {
    font-size: 3rem;
  }

  .error-subtitle {
    font-size: 1.2rem;
  }

  .error-actions {
    flex-direction: column;
    align-items: center;
  }

  .btn {
    width: 200px;
    justify-content: center;
  }

  .quick-links {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .error-title {
    font-size: 2.5rem;
  }

  .error-content {
    padding: 20px 15px;
  }
}
</style>
