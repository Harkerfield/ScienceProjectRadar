<template>
  <div class="detection-log">
    <div v-if="detections.length === 0" class="no-detections">
      <i class="fas fa-search text-muted me-2"></i>
      <span class="text-muted">No detections recorded</span>
    </div>

    <div v-else class="detection-list">
      <div
        v-for="(detection, index) in displayDetections"
        :key="`${detection.timestamp}-${index}`"
        :class="['detection-item', getDetectionClass(detection)]"
      >
        <div class="detection-source">
          <i :class="getSourceIcon(detection.source)"></i>
          <span class="source-label">{{ getSourceLabel(detection.source) }}</span>
        </div>

        <div class="detection-data">
          <div class="detection-position">
            <span class="distance">{{ detection.distance }}m</span>
            <span class="angle">{{ detection.angle }}°</span>
          </div>

          <div class="detection-strength" v-if="detection.strength">
            <div class="strength-bar">
              <div
                class="strength-fill"
                :style="{ width: Math.min(100, (detection.strength / 100) * 100) + '%' }"
              ></div>
            </div>
            <span class="strength-value">{{ detection.strength }}%</span>
          </div>
        </div>

        <div class="detection-time">
          <small class="text-muted">{{ formatTime(detection.timestamp) }}</small>
        </div>
      </div>

      <div v-if="detections.length > maxDisplay" class="more-detections">
        <small class="text-muted">
          <i class="fas fa-ellipsis-h me-1"></i>
          {{ detections.length - maxDisplay }} more detections...
        </small>
      </div>
    </div>

    <!-- Summary Stats -->
    <div class="detection-summary mt-3" v-if="detections.length > 0">
      <div class="summary-grid">
        <div class="summary-item">
          <span class="summary-label">Total:</span>
          <span class="summary-value">{{ detections.length }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Avg Distance:</span>
          <span class="summary-value">{{ avgDistance }}m</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">Range:</span>
          <span class="summary-value">{{ minDistance }}-{{ maxDistance }}m</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DetectionLog',

  props: {
    detections: {
      type: Array,
      default: () => []
    },
    maxDisplay: {
      type: Number,
      default: 10
    }
  },

  computed: {
    displayDetections() {
      // Create local copy to avoid mutating props
      return [...this.detections]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, this.maxDisplay)
    },

    avgDistance() {
      if (this.detections.length === 0) return 0
      const sum = this.detections.reduce((acc, d) => acc + (d.distance || 0), 0)
      return Math.round((sum / this.detections.length) * 10) / 10
    },

    minDistance() {
      if (this.detections.length === 0) return 0
      return Math.min(...this.detections.map(d => d.distance || 0))
    },

    maxDistance() {
      if (this.detections.length === 0) return 0
      return Math.max(...this.detections.map(d => d.distance || 0))
    }
  },

  methods: {
    getDetectionClass(detection) {
      const age = Date.now() - new Date(detection.timestamp).getTime()
      const classes = ['detection-entry']

      // Add source class
      if (detection.source) {
        classes.push(`source-${detection.source}`)
      }

      // Add age class for fading effect
      if (age < 5000) {
        classes.push('recent')
      } else if (age < 30000) {
        classes.push('moderate')
      } else {
        classes.push('old')
      }

      // Add strength class
      if (detection.strength) {
        if (detection.strength > 80) {
          classes.push('strength-high')
        } else if (detection.strength > 50) {
          classes.push('strength-medium')
        } else {
          classes.push('strength-low')
        }
      }

      return classes.join(' ')
    },

    getSourceIcon(source) {
      const icons = {
        local: 'fas fa-satellite-dish text-success',
        pico: 'fas fa-microchip text-warning',
        manual: 'fas fa-hand-pointer text-info'
      }
      return icons[source] || 'fas fa-circle text-secondary'
    },

    getSourceLabel(source) {
      const labels = {
        local: 'Local',
        pico: 'Pico',
        manual: 'Manual'
      }
      return labels[source] || 'Unknown'
    },

    formatTime(timestamp) {
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now.getTime() - date.getTime()

      if (diff < 60000) {
        return 'Just now'
      } else if (diff < 3600000) {
        return `${Math.floor(diff / 60000)}m ago`
      } else if (diff < 86400000) {
        return `${Math.floor(diff / 3600000)}h ago`
      } else {
        return date.toLocaleDateString()
      }
    }
  }
}
</script>

<style scoped>
.detection-log {
  max-height: 400px;
  overflow-y: auto;
}

.no-detections {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
}

.detection-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.detection-item {
  display: flex;
  align-items: center;
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.02);
  border-left: 3px solid #dee2e6;
  border-radius: 0.375rem;
  transition: all 0.3s ease;
}

.detection-item:hover {
  background: rgba(0, 0, 0, 0.05);
  transform: translateX(2px);
}

/* Source-specific styling */
.source-local {
  border-left-color: #28a745;
  background: rgba(40, 167, 69, 0.05);
}

.source-pico {
  border-left-color: #fd7e14;
  background: rgba(253, 126, 20, 0.05);
}

.source-manual {
  border-left-color: #17a2b8;
  background: rgba(23, 162, 184, 0.05);
}

/* Age-based opacity */
.recent {
  opacity: 1;
}

.moderate {
  opacity: 0.8;
}

.old {
  opacity: 0.6;
}

/* Strength-based glow effect */
.strength-high {
  box-shadow: 0 0 8px rgba(220, 53, 69, 0.3);
}

.strength-medium {
  box-shadow: 0 0 5px rgba(255, 193, 7, 0.3);
}

.strength-low {
  box-shadow: 0 0 3px rgba(108, 117, 125, 0.3);
}

.detection-source {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 80px;
}

.source-label {
  font-size: 0.875rem;
  font-weight: 500;
}

.detection-data {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  margin: 0 1rem;
}

.detection-position {
  display: flex;
  gap: 1rem;
  font-family: 'Courier New', monospace;
}

.distance {
  color: #28a745;
  font-weight: bold;
}

.angle {
  color: #17a2b8;
  font-weight: bold;
}

.detection-strength {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.strength-bar {
  width: 60px;
  height: 4px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.strength-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #ffc107, #dc3545);
  border-radius: 2px;
  transition: width 0.3s ease;
}

.strength-value {
  font-size: 0.75rem;
  color: #6c757d;
  min-width: 30px;
}

.detection-time {
  min-width: 80px;
  text-align: right;
}

.more-detections {
  text-align: center;
  padding: 0.5rem;
  border-top: 1px solid #dee2e6;
  margin-top: 0.5rem;
}

.detection-summary {
  padding: 0.75rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 0.375rem;
  border-top: 1px solid #dee2e6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 0.75rem;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.summary-label {
  font-size: 0.75rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.summary-value {
  font-weight: bold;
  color: #495057;
  font-family: 'Courier New', monospace;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .detection-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .detection-source,
  .detection-time {
    min-width: auto;
    width: 100%;
  }

  .detection-time {
    text-align: left;
  }

  .detection-data {
    margin: 0;
    width: 100%;
  }

  .summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Scrollbar styling */
.detection-log::-webkit-scrollbar {
  width: 6px;
}

.detection-log::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.detection-log::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.detection-log::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

/* Animation for new detections */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.detection-item.recent {
  animation: slideIn 0.3s ease-out;
}
</style>
