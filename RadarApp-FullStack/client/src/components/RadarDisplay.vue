<template>
  <div class="radar-display" ref="radarContainer">
    <canvas
      ref="radarCanvas"
      :width="canvasSize"
      :height="canvasSize"
      @mousemove="handleMouseMove"
      @click="handleClick"
    ></canvas>

    <!-- Radar Information Overlay -->
    <div class="radar-info">
      <div class="radar-stats">
        <div class="stat-item">
          <span class="stat-label">Range:</span>
          <span class="stat-value">{{ range }}m</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Sweep:</span>
          <span class="stat-value">{{ sweepAngle.toFixed(1) }}°</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Targets:</span>
          <span class="stat-value">{{ activeTargets }}</span>
        </div>
      </div>
    </div>

    <!-- Crosshair and mouse position -->
    <div
      v-if="mousePosition"
      class="radar-crosshair"
      :style="{
        left: mousePosition.x + 'px',
        top: mousePosition.y + 'px'
      }"
    >
      <div class="crosshair-info">
        {{ mouseDistance }}m @ {{ mouseAngle }}°
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'RadarDisplay',

  props: {
    radarData: {
      type: Array,
      default: () => []
    },
    isScanning: {
      type: Boolean,
      default: false
    },
    range: {
      type: Number,
      default: 100
    },
    sweepAngle: {
      type: Number,
      default: 0
    }
  },

  data() {
    return {
      canvasSize: 400,
      centerX: 200,
      centerY: 200,
      radarRadius: 180,
      animationFrame: null,
      mousePosition: null,
      mouseDistance: 0,
      mouseAngle: 0,
      fadeTargets: new Map(), // Store fading targets
      sweepTrail: []
    }
  },

  computed: {
    activeTargets() {
      return this.radarData.filter(data => data.detected && this.isTargetVisible(data)).length
    },

    scaleFactor() {
      return this.radarRadius / this.range
    }
  },

  mounted() {
    this.initCanvas()
    this.startAnimation()
    window.addEventListener('resize', this.handleResize)
  },

  beforeUnmount() {
    this.stopAnimation()
    window.removeEventListener('resize', this.handleResize)
  },

  watch: {
    radarData: {
      handler() {
        this.updateTargets()
      },
      deep: true
    }
  },

  methods: {
    initCanvas() {
      this.handleResize()
      this.drawRadar()
    },

    handleResize() {
      const container = this.$refs.radarContainer
      if (container) {
        const size = Math.min(container.clientWidth, container.clientHeight, 600)
        this.canvasSize = size
        this.centerX = size / 2
        this.centerY = size / 2
        this.radarRadius = (size / 2) * 0.9

        this.$nextTick(() => {
          this.drawRadar()
        })
      }
    },

    startAnimation() {
      const animate = () => {
        this.drawRadar()
        this.animationFrame = requestAnimationFrame(animate)
      }
      animate()
    },

    stopAnimation() {
      if (this.animationFrame) {
        cancelAnimationFrame(this.animationFrame)
        this.animationFrame = null
      }
    },

    drawRadar() {
      const canvas = this.$refs.radarCanvas
      if (!canvas) return

      const ctx = canvas.getContext('2d')

      // Clear canvas
      ctx.fillStyle = '#0a0a0a'
      ctx.fillRect(0, 0, this.canvasSize, this.canvasSize)

      // Draw range rings
      this.drawRangeRings(ctx)

      // Draw grid lines
      this.drawGridLines(ctx)

      // Draw scale labels
      this.drawScaleLabels(ctx)

      // Draw sweep beam
      if (this.isScanning) {
        this.drawSweepBeam(ctx)
      }

      // Draw targets
      this.drawTargets(ctx)

      // Draw fading targets
      this.drawFadingTargets(ctx)

      // Draw center dot
      this.drawCenter(ctx)
    },

    drawRangeRings(ctx) {
      ctx.strokeStyle = '#1a4a3a'
      ctx.lineWidth = 1

      const rings = 5
      for (let i = 1; i <= rings; i++) {
        const radius = (this.radarRadius / rings) * i

        ctx.beginPath()
        ctx.arc(this.centerX, this.centerY, radius, 0, Math.PI * 2)
        ctx.stroke()
      }
    },

    drawGridLines(ctx) {
      ctx.strokeStyle = '#1a3a2a'
      ctx.lineWidth = 0.5

      // Draw cardinal directions
      const directions = [0, 45, 90, 135, 180, 225, 270, 315]

      directions.forEach(angle => {
        const radian = (angle * Math.PI) / 180
        const x1 = this.centerX + Math.cos(radian - Math.PI / 2) * 10
        const y1 = this.centerY + Math.sin(radian - Math.PI / 2) * 10
        const x2 = this.centerX + Math.cos(radian - Math.PI / 2) * this.radarRadius
        const y2 = this.centerY + Math.sin(radian - Math.PI / 2) * this.radarRadius

        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.stroke()
      })
    },

    drawScaleLabels(ctx) {
      ctx.fillStyle = '#4a9a6a'
      ctx.font = '12px monospace'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'

      // Distance labels
      const rings = 5
      for (let i = 1; i <= rings; i++) {
        const radius = (this.radarRadius / rings) * i
        const distance = (this.range / rings) * i

        ctx.fillText(
          distance + 'm',
          this.centerX + radius * 0.707,
          this.centerY - radius * 0.707 - 10
        )
      }

      // Direction labels
      const labels = [
        { angle: 0, text: 'N' },
        { angle: 90, text: 'E' },
        { angle: 180, text: 'S' },
        { angle: 270, text: 'W' }
      ]

      labels.forEach(({ angle, text }) => {
        const radian = (angle * Math.PI) / 180
        const x = this.centerX + Math.cos(radian - Math.PI / 2) * (this.radarRadius + 20)
        const y = this.centerY + Math.sin(radian - Math.PI / 2) * (this.radarRadius + 20)

        ctx.fillStyle = '#6aaa8a'
        ctx.font = 'bold 14px monospace'
        ctx.fillText(text, x, y)
      })
    },

    drawSweepBeam(ctx) {
      const sweepRadian = (this.sweepAngle * Math.PI) / 180

      // Draw sweep beam
      const gradient = ctx.createRadialGradient(
        this.centerX, this.centerY, 0,
        this.centerX, this.centerY, this.radarRadius
      )
      gradient.addColorStop(0, 'rgba(0, 255, 0, 0.3)')
      gradient.addColorStop(0.5, 'rgba(0, 255, 0, 0.1)')
      gradient.addColorStop(1, 'rgba(0, 255, 0, 0)')

      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.moveTo(this.centerX, this.centerY)
      ctx.arc(
        this.centerX, this.centerY,
        this.radarRadius,
        sweepRadian - Math.PI / 2 - 0.1,
        sweepRadian - Math.PI / 2 + 0.1
      )
      ctx.closePath()
      ctx.fill()

      // Draw sweep line
      ctx.strokeStyle = '#00ff00'
      ctx.lineWidth = 2
      ctx.beginPath()
      ctx.moveTo(this.centerX, this.centerY)
      ctx.lineTo(
        this.centerX + Math.cos(sweepRadian - Math.PI / 2) * this.radarRadius,
        this.centerY + Math.sin(sweepRadian - Math.PI / 2) * this.radarRadius
      )
      ctx.stroke()
    },

    drawTargets(ctx) {
      this.radarData.forEach(data => {
        if (data.detected && this.isTargetVisible(data)) {
          this.drawTarget(ctx, data)
        }
      })
    },

    drawTarget(ctx, data) {
      const angle = data.angle || 0
      const distance = data.distance || 0
      const radian = (angle * Math.PI) / 180

      if (distance > this.range) return

      const x = this.centerX + Math.cos(radian - Math.PI / 2) * (distance * this.scaleFactor)
      const y = this.centerY + Math.sin(radian - Math.PI / 2) * (distance * this.scaleFactor)

      // Determine color based on source and signal strength
      let color = '#ff4444' // Default red for detections
      let size = 4

      if (data.source === 'pico') {
        color = '#ff6b35' // Orange for Pico
      } else if (data.source === 'local') {
        color = '#44ff44' // Green for local
      }

      // Adjust size based on signal strength if available
      if (data.strength) {
        size = Math.max(3, Math.min(8, data.strength / 10))
      }

      // Draw target
      ctx.fillStyle = color
      ctx.beginPath()
      ctx.arc(x, y, size, 0, Math.PI * 2)
      ctx.fill()

      // Add pulsing effect for recent targets
      const age = Date.now() - new Date(data.timestamp).getTime()
      if (age < 2000) { // Pulse for 2 seconds
        const pulseAlpha = Math.max(0, 1 - (age / 2000))
        ctx.strokeStyle = color.replace(')', `, ${pulseAlpha})`)
        ctx.lineWidth = 2
        ctx.beginPath()
        ctx.arc(x, y, size + 3, 0, Math.PI * 2)
        ctx.stroke()
      }

      // Draw distance/angle info on hover
      if (this.isNearMouse(x, y)) {
        this.drawTargetInfo(ctx, x, y, data)
      }
    },

    drawTargetInfo(ctx, x, y, data) {
      const text = `${data.distance}m @ ${data.angle}°`
      ctx.fillStyle = 'rgba(0, 0, 0, 0.8)'
      ctx.fillRect(x + 10, y - 15, 80, 20)

      ctx.fillStyle = '#ffffff'
      ctx.font = '10px monospace'
      ctx.textAlign = 'left'
      ctx.fillText(text, x + 12, y - 5)
    },

    drawFadingTargets(ctx) {
      const currentTime = Date.now()
      const toRemove = []

      this.fadeTargets.forEach((target, key) => {
        const age = currentTime - target.timestamp
        const fadeTime = 5000 // 5 seconds fade

        if (age > fadeTime) {
          toRemove.push(key)
          return
        }

        const alpha = Math.max(0, 1 - (age / fadeTime))
        const radian = (target.angle * Math.PI) / 180
        const x = this.centerX + Math.cos(radian - Math.PI / 2) * (target.distance * this.scaleFactor)
        const y = this.centerY + Math.sin(radian - Math.PI / 2) * (target.distance * this.scaleFactor)

        ctx.fillStyle = `rgba(255, 255, 0, ${alpha * 0.6})`
        ctx.beginPath()
        ctx.arc(x, y, 2, 0, Math.PI * 2)
        ctx.fill()
      })

      // Remove expired targets
      toRemove.forEach(key => this.fadeTargets.delete(key))
    },

    drawCenter(ctx) {
      ctx.fillStyle = '#00ff00'
      ctx.beginPath()
      ctx.arc(this.centerX, this.centerY, 3, 0, Math.PI * 2)
      ctx.fill()
    },

    isTargetVisible(data) {
      // Check if target is within current sweep angle (simulate radar sweep)
      const targetAge = Date.now() - new Date(data.timestamp).getTime()
      return targetAge < 10000 // Show targets for 10 seconds
    },

    isNearMouse(x, y) {
      if (!this.mousePosition) return false
      const dx = x - this.mousePosition.x
      const dy = y - this.mousePosition.y
      return Math.sqrt(dx * dx + dy * dy) < 15
    },

    updateTargets() {
      // Add new detections to fading targets
      this.radarData.forEach(data => {
        if (data.detected) {
          const key = `${data.angle}_${data.distance}_${data.timestamp}`
          if (!this.fadeTargets.has(key)) {
            this.fadeTargets.set(key, {
              ...data,
              timestamp: Date.now()
            })
          }
        }
      })
    },

    handleMouseMove(event) {
      const rect = this.$refs.radarCanvas.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top

      // Calculate distance and angle from center
      const dx = x - this.centerX
      const dy = y - this.centerY
      const distance = Math.sqrt(dx * dx + dy * dy)
      const angle = (Math.atan2(dy, dx) * 180 / Math.PI + 90 + 360) % 360

      // Set position for crosshair - CSS transform will center it
      this.mousePosition = { x, y }
      this.mouseDistance = Math.round((distance / this.scaleFactor) * 10) / 10
      this.mouseAngle = Math.round(angle)
    },

    handleClick(_event) {
      // Could be used for manual target marking or other interactions
      this.$emit('radar-click', {
        distance: this.mouseDistance,
        angle: this.mouseAngle
      })
    }
  }
}
</script>

<style scoped>
.radar-display {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0a0a0a;
  border-radius: 8px;
  overflow: hidden;
}

canvas {
  border-radius: 50%;
  cursor: crosshair;
  box-shadow:
    0 0 20px rgba(0, 255, 0, 0.3),
    inset 0 0 20px rgba(0, 255, 0, 0.1);
}

.radar-info {
  position: absolute;
  top: 15px;
  left: 15px;
  background: rgba(0, 0, 0, 0.8);
  border-radius: 6px;
  padding: 10px;
  border: 1px solid rgba(0, 255, 0, 0.3);
}

.radar-stats {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.stat-label {
  color: #4a9a6a;
  min-width: 50px;
}

.stat-value {
  color: #00ff00;
  font-weight: bold;
}

.radar-crosshair {
  position: absolute;
  pointer-events: none;
  z-index: 10;
  transform: translate(-50%, -50%);
}

.radar-crosshair::before,
.radar-crosshair::after {
  content: '';
  position: absolute;
  background: rgba(0, 255, 0, 0.9);
  box-shadow: 0 0 5px rgba(0, 255, 0, 0.8);
}

.radar-crosshair::before {
  width: 24px;
  height: 2px;
  top: -1px;
  left: -1px;
}

.radar-crosshair::after {
  width: 2px;
  height: 24px;
  top: -1px;
  left: -1px;
}

.crosshair-info {
  position: absolute;
  top: -28px;
  left: 12px;
  background: rgba(0, 0, 0, 0.95);
  color: #00ff00;
  padding: 4px 8px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  white-space: nowrap;
  border: 1px solid rgba(0, 255, 0, 0.6);
  box-shadow: 0 0 8px rgba(0, 255, 0, 0.3);
}

@media (max-width: 768px) {
  .radar-display {
    min-height: 300px;
  }

  .radar-info {
    top: 10px;
    left: 10px;
    padding: 8px;
  }

  .stat-item {
    font-size: 11px;
  }
}
</style>
