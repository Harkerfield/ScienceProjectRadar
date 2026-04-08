<template>
  <div class="stepper-control">
    <div class="page-header">
      <h1>Stepper Motor Control</h1>
      <div class="connection-status">
        <span class="status-indicator" :class="{ connected: stepperConnected }"></span>
        <span>{{ stepperConnected ? 'Connected' : 'Disconnected' }}</span>
      </div>
    </div>

    <div class="control-panels">
      <!-- Motor Status Panel -->
      <div class="card motor-status">
        <h2>Motor Status</h2>
        <div class="status-grid">
          <div class="status-item">
            <span class="label">Current Position:</span>
            <span class="value">{{ currentPosition }}°</span>
          </div>
          <div class="status-item">
            <span class="label">Target Position:</span>
            <span class="value">{{ targetPosition }}°</span>
          </div>
          <div class="status-item">
            <span class="label">Motor State:</span>
            <span class="value" :class="motorStateClass">{{ motorState }}</span>
          </div>
          <div class="status-item">
            <span class="label">Speed:</span>
            <span class="value">{{ currentSpeed }} RPM</span>
          </div>
        </div>
      </div>

      <!-- Manual Control Panel -->
      <div class="card manual-control">
        <h2>Manual Control</h2>
        <div class="control-section">
          <div class="position-control">
            <label for="targetPos">Target Position (0-360°):</label>
            <div class="input-group">
              <input
                id="targetPos"
                v-model.number="manualTargetPosition"
                type="number"
                min="0"
                max="360"
                step="1"
                :disabled="!stepperConnected || isMoving"
              />
              <button
                @click="moveToPosition"
                :disabled="!stepperConnected || isMoving"
                class="btn btn-primary"
              >
                Move
              </button>
            </div>
          </div>

          <div class="speed-control">
            <label for="speed">Speed (RPM):</label>
            <input
              id="speed"
              v-model.number="motorSpeed"
              type="range"
              min="1"
              max="100"
              step="1"
              :disabled="!stepperConnected"
            />
            <span class="speed-display">{{ motorSpeed }} RPM</span>
          </div>

          <div class="direction-buttons">
            <button
              @click="rotateClockwise"
              :disabled="!stepperConnected || isMoving"
              class="btn btn-secondary"
            >
              Rotate CW
            </button>
            <button
              @click="rotateCounterClockwise"
              :disabled="!stepperConnected || isMoving"
              class="btn btn-secondary"
            >
              Rotate CCW
            </button>
            <button
              @click="stopMotor"
              :disabled="!stepperConnected"
              class="btn btn-danger"
            >
              Stop
            </button>
          </div>
        </div>
      </div>

      <!-- Preset Positions Panel -->
      <div class="card preset-positions">
        <h2>Preset Positions</h2>
        <div class="preset-grid">
          <button
            v-for="preset in presetPositions"
            :key="preset.name"
            @click="moveToPreset(preset.angle)"
            :disabled="!stepperConnected || isMoving"
            class="preset-btn"
          >
            {{ preset.name }}
            <span class="preset-angle">{{ preset.angle }}°</span>
          </button>
        </div>

        <div class="preset-controls">
          <button
            @click="saveCurrentPosition"
            :disabled="!stepperConnected"
            class="btn btn-outline"
          >
            Save Current Position
          </button>
          <button
            @click="homeMotor"
            :disabled="!stepperConnected || isMoving"
            class="btn btn-outline"
          >
            Home Motor
          </button>
        </div>
      </div>

      <!-- Configuration Panel -->
      <div class="card configuration">
        <h2>Motor Configuration</h2>
        <div class="config-section">
          <div class="config-item">
            <label for="acceleration">Acceleration:</label>
            <input
              id="acceleration"
              v-model.number="motorConfig.acceleration"
              type="number"
              min="1"
              max="1000"
              :disabled="!stepperConnected"
            />
          </div>
          <div class="config-item">
            <label for="deceleration">Deceleration:</label>
            <input
              id="deceleration"
              v-model.number="motorConfig.deceleration"
              type="number"
              min="1"
              max="1000"
              :disabled="!stepperConnected"
            />
          </div>
          <div class="config-item">
            <label for="microstepping">Microstepping:</label>
            <select
              id="microstepping"
              v-model="motorConfig.microstepping"
              :disabled="!stepperConnected"
            >
              <option value="1">1 (Full Step)</option>
              <option value="2">1/2 Step</option>
              <option value="4">1/4 Step</option>
              <option value="8">1/8 Step</option>
              <option value="16">1/16 Step</option>
            </select>
          </div>
          <button
            @click="applyConfiguration"
            :disabled="!stepperConnected"
            class="btn btn-primary"
          >
            Apply Configuration
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'StepperControl',

  data() {
    return {
      manualTargetPosition: 0,
      motorSpeed: 50,
      motorConfig: {
        acceleration: 100,
        deceleration: 100,
        microstepping: 8
      },
      presetPositions: [
        { name: 'Home', angle: 0 },
        { name: 'Quarter', angle: 90 },
        { name: 'Half', angle: 180 },
        { name: 'Three Quarter', angle: 270 }
      ]
    }
  },

  computed: {
    ...mapGetters('stepper', [
      'currentPosition',
      'targetPosition',
      'motorState',
      'currentSpeed',
      'isMoving'
    ]),
    ...mapGetters('connection', [
      'stepperConnected'
    ]),

    motorStateClass() {
      return {
        'state-idle': this.motorState === 'idle',
        'state-moving': this.motorState === 'moving',
        'state-error': this.motorState === 'error'
      }
    }
  },

  methods: {
    ...mapActions('stepper', [
      'moveToAngle',
      'rotateDirection',
      'stopRotation',
      'homePosition',
      'updateConfiguration'
    ]),

    moveToPosition() {
      if (this.manualTargetPosition >= 0 && this.manualTargetPosition <= 360) {
        this.moveToAngle({
          angle: this.manualTargetPosition,
          speed: this.motorSpeed
        })
      }
    },

    moveToPreset(angle) {
      this.moveToAngle({
        angle,
        speed: this.motorSpeed
      })
    },

    rotateClockwise() {
      this.rotateDirection({
        direction: 'cw',
        speed: this.motorSpeed
      })
    },

    rotateCounterClockwise() {
      this.rotateDirection({
        direction: 'ccw',
        speed: this.motorSpeed
      })
    },

    stopMotor() {
      this.stopRotation()
    },

    homeMotor() {
      this.homePosition()
    },

    saveCurrentPosition() {
      const name = prompt('Enter name for this position:')
      if (name && name.trim()) {
        this.presetPositions.push({
          name: name.trim(),
          angle: this.currentPosition
        })
      }
    },

    applyConfiguration() {
      this.updateConfiguration(this.motorConfig)
    }
  }
}
</script>

<style scoped>
.stepper-control {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-header h1 {
  margin: 0;
  color: #333;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #f44336;
}

.status-indicator.connected {
  background-color: #4caf50;
}

.control-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card h2 {
  margin: 0 0 20px 0;
  color: #333;
  font-size: 18px;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-item .label {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
}

.status-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.value.state-idle {
  color: #666;
}

.value.state-moving {
  color: #2196f3;
}

.value.state-error {
  color: #f44336;
}

.control-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.position-control label,
.speed-control label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.input-group {
  display: flex;
  gap: 10px;
}

.input-group input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.speed-control {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.speed-control input[type="range"] {
  width: 100%;
}

.speed-display {
  align-self: flex-end;
  font-weight: 500;
  color: #333;
}

.direction-buttons {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 20px;
}

.preset-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.preset-btn:hover:not(:disabled) {
  background: #e0e0e0;
}

.preset-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.preset-angle {
  font-size: 12px;
  color: #666;
}

.preset-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.config-section {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item label {
  font-weight: 500;
  color: #333;
}

.config-item input,
.config-item select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #2196f3;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1976d2;
}

.btn-secondary {
  background: #666;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #555;
}

.btn-danger {
  background: #f44336;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #d32f2f;
}

.btn-outline {
  background: transparent;
  color: #2196f3;
  border: 1px solid #2196f3;
}

.btn-outline:hover:not(:disabled) {
  background: #2196f3;
  color: white;
}
</style>
