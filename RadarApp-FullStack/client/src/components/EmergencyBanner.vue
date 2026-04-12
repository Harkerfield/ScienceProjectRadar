<template>
  <transition name="emergency-banner">
    <div v-if="emergencyNotifications.length > 0" class="emergency-banner">
      <div class="emergency-banner-content">
        <div class="emergency-icon">
          <i class="fas fa-exclamation-circle"></i>
        </div>
        <div class="emergency-text">
          <h5 class="emergency-title">
            {{ emergencyNotifications[0].title }}
          </h5>
          <p class="emergency-message">
            {{ emergencyNotifications[0].message }}
          </p>
        </div>
        <div class="emergency-actions">
          <button
            @click="dismissEmergency"
            class="btn btn-danger btn-sm"
          >
            <i class="fas fa-times me-1"></i>
            Clear
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'EmergencyBanner',

  computed: {
    ...mapGetters('notifications', ['emergencyNotifications'])
  },

  methods: {
    ...mapActions('notifications', ['dismissNotification']),

    dismissEmergency() {
      if (this.emergencyNotifications.length > 0) {
        this.dismissNotification(this.emergencyNotifications[0].id)
      }
    }
  }
}
</script>

<style scoped>
.emergency-banner {
  position: fixed;
  top: 60px;
  left: 0;
  right: 0;
  background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
  color: white;
  z-index: 1060;
  box-shadow: 0 6px 20px rgba(220, 53, 69, 0.3);
  animation: slideDown 0.3s ease-out;
}

.emergency-banner-content {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.emergency-icon {
  flex-shrink: 0;
  font-size: 28px;
  animation: pulse 1s infinite;
}

.emergency-text {
  flex: 1;
  min-width: 0;
}

.emergency-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
}

.emergency-message {
  margin: 4px 0 0 0;
  font-size: 14px;
  opacity: 0.95;
  line-height: 1.3;
}

.emergency-actions {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}

.emergency-banner .btn {
  font-weight: 600;
}

.emergency-banner .btn-danger {
  background-color: rgba(255, 255, 255, 0.2);
  border-color: white;
  color: white;
  transition: all 0.2s ease;
}

.emergency-banner .btn-danger:hover {
  background-color: white;
  color: #dc3545;
  border-color: white;
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
}

.emergency-banner-enter-active,
.emergency-banner-leave-active {
  transition: all 0.3s ease;
}

.emergency-banner-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.emergency-banner-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .emergency-banner-content {
    flex-direction: column;
    align-items: flex-start;
    padding: 12px 16px;
  }

  .emergency-title {
    font-size: 16px;
  }

  .emergency-message {
    font-size: 12px;
  }

  .emergency-actions {
    width: 100%;
    margin-top: 8px;
  }

  .emergency-actions .btn {
    flex: 1;
  }
}
</style>
