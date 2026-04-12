<template>
  <teleport to="body">
    <transition-group
      name="notification"
      tag="div"
      class="notification-container"
    >
      <div
        v-for="notification in activeNotifications"
        :key="notification.id"
        :class="[
          'notification',
          `notification-${notification.type}`,
          { 'notification-dismissible': notification.dismissible }
        ]"
        @click="handleNotificationClick(notification)"
      >
        <div class="notification-content">
          <!-- Icon -->
          <div class="notification-icon">
            <i :class="getIconClass(notification.type)"></i>
          </div>

          <!-- Content -->
          <div class="notification-body">
            <h5 v-if="notification.title" class="notification-title">
              {{ notification.title }}
            </h5>
            <p class="notification-message">
              {{ notification.message }}
            </p>
            <small v-if="notification.timestamp" class="notification-time">
              {{ formatTime(notification.timestamp) }}
            </small>
          </div>

          <!-- Actions -->
          <div class="notification-actions">
            <button
              v-if="notification.action"
              @click.stop="handleAction(notification)"
              class="btn btn-sm btn-outline-primary notification-action-btn"
            >
              {{ notification.action.text }}
            </button>

            <button
              v-if="notification.dismissible !== false"
              @click.stop="dismissNotification(notification.id)"
              class="btn btn-sm notification-close"
              aria-label="Close"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>

        <!-- Progress bar for auto-dismiss -->
        <div
          v-if="notification.duration && notification.duration > 0"
          class="notification-progress"
          :style="{ animationDuration: `${notification.duration}ms` }"
        ></div>
      </div>
    </transition-group>
  </teleport>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'NotificationContainer',

  computed: {
    ...mapGetters('notifications', ['notifications']),

    activeNotifications() {
      // Filter out emergency notifications since they're shown in EmergencyBanner
      return this.notifications.filter(n => n.type !== 'emergency')
    }
  },

  methods: {
    ...mapActions('notifications', ['removeNotification']),

    getIconClass(type) {
      const iconMap = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle',
        loading: 'fas fa-spinner fa-spin',
        emergency: 'fas fa-exclamation-octagon'
      }
      return iconMap[type] || 'fas fa-bell'
    },

    formatTime(timestamp) {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      })
    },

    handleNotificationClick(notification) {
      if (notification.clickable) {
        this.handleAction(notification)
      }
    },

    handleAction(notification) {
      if (notification.action && typeof notification.action.handler === 'function') {
        notification.action.handler()
      }

      // Auto-dismiss after action if specified
      if (notification.action && notification.action.dismissAfter) {
        this.dismissNotification(notification.id)
      }
    },

    dismissNotification(id) {
      this.removeNotification(id)
    }
  }
}
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 80px; /* Below navbar */
  right: 20px;
  z-index: 1050;
  width: 350px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  pointer-events: none;
}

.notification {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  margin-bottom: 12px;
  overflow: hidden;
  position: relative;
  pointer-events: auto;
  cursor: default;
  border-left: 4px solid #ccc;
}

.notification-success {
  border-left-color: #28a745;
}

.notification-error {
  border-left-color: #dc3545;
}

.notification-warning {
  border-left-color: #ffc107;
}

.notification-info {
  border-left-color: #17a2b8;
}

.notification-loading {
  border-left-color: #6f42c1;
}

.notification-emergency {
  border-left-color: #dc3545;
  background: linear-gradient(135deg, rgba(220, 53, 69, 0.05) 0%, rgba(220, 53, 69, 0.02) 100%);
}

.notification-dismissible {
  cursor: pointer;
}

.notification-content {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  gap: 12px;
}

.notification-icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 2px;
}

.notification-success .notification-icon {
  color: #28a745;
}

.notification-error .notification-icon {
  color: #dc3545;
}

.notification-warning .notification-icon {
  color: #ffc107;
}

.notification-info .notification-icon {
  color: #17a2b8;
}

.notification-loading .notification-icon {
  color: #6f42c1;
}

.notification-emergency .notification-icon {
  color: #dc3545;
}

.notification-body {
  flex: 1;
  min-width: 0;
}

.notification-title {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
  line-height: 1.3;
}

.notification-message {
  margin: 0 0 4px 0;
  font-size: 13px;
  color: #666;
  line-height: 1.4;
  word-wrap: break-word;
}

.notification-time {
  font-size: 11px;
  color: #999;
}

.notification-actions {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.notification-action-btn {
  font-size: 11px;
  padding: 4px 8px;
  white-space: nowrap;
}

.notification-close {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 3px;
  transition: all 0.2s;
}

.notification-close:hover {
  background: #f8f9fa;
  color: #666;
}

.notification-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    rgba(0, 0, 0, 0.1) 0%,
    rgba(0, 0, 0, 0.2) 100%
  );
  animation: notification-progress linear forwards;
}

@keyframes notification-progress {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

/* Transition animations */
.notification-enter-active {
  transition: all 0.3s ease-out;
}

.notification-leave-active {
  transition: all 0.3s ease-in;
}

.notification-enter-from {
  transform: translateX(100%);
  opacity: 0;
}

.notification-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.notification-move {
  transition: transform 0.3s ease;
}

/* Responsive design */
@media (max-width: 480px) {
  .notification-container {
    top: 70px;
    right: 10px;
    left: 10px;
    width: auto;
  }

  .notification-content {
    padding: 12px;
  }

  .notification-title {
    font-size: 13px;
  }

  .notification-message {
    font-size: 12px;
  }
}

/* Dark theme support */
@media (prefers-color-scheme: dark) {
  .notification {
    background: #2d3748;
    color: #e2e8f0;
  }

  .notification-title {
    color: #f7fafc;
  }

  .notification-message {
    color: #cbd5e0;
  }

  .notification-time {
    color: #a0aec0;
  }

  .notification-close:hover {
    background: #4a5568;
    color: #e2e8f0;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .notification {
    border: 2px solid #000;
  }

  .notification-close {
    border: 1px solid currentColor;
  }
}
</style>
