# HB100 Doppler Radar Sensor Test
# MicroPython test script for Raspberry Pi Pico
# Tests the HB100 10.525GHz Doppler Effect Microwave Motion Sensor
# Works with both standalone HB100 and CQRobot versions

from machine import ADC, Pin, PWM, Timer
import utime
import math

print("=" * 70)
print("HB100 DOPPLER RADAR SENSOR TEST")
print("10.525GHz Microwave Motion Sensor (SKU: CQRSENWB01)")
print("=" * 70)
print()

# ============================================================
# HB100 PINOUT CONFIGURATION
# ============================================================
# Adjust these pins based on your actual wiring

# Option 1: Analog IF Output (most common)
# Connect HB100 IF output to an ADC pin
IF_PIN = 27                 # ADC1 on Pico (GPIO27)
IF_ADC = ADC(Pin(IF_PIN))   # Analog intermediate frequency output

# Option 2: Motion Detection Pin (if available on your version)
MOTION_PIN = 26             # Digital motion detection pin

# LED indicator
led = Pin("LED", Pin.OUT)
led.on()

print("HB100 Configuration:")
print(f"  IF Output Pin:     GPIO{IF_PIN} (ADC1)")
print(f"  Motion Pin:        GPIO{MOTION_PIN}")
print(f"  Status LED:        GPIO25")
print()
print("Connections:")
print("  HB100 VCC:         3.3V on Pico")
print("  HB100 GND:         GND on Pico")
print("  HB100 IF Output:   GPIO27 (ADC1)")
print("  HB100 Motion:      GPIO26 (optional)")
print("=" * 70)
print()

# ============================================================
# SENSOR READING FUNCTIONS
# ============================================================

class HB100Sensor:
    """HB100 Doppler Radar Sensor Reader"""
    
    def __init__(self, if_pin=27, motion_pin=26):
        """Initialize sensor
        
        Args:
            if_pin: GPIO pin connected to IF output (ADC)
            motion_pin: GPIO pin for motion detection (optional)
        """
        self.if_adc = ADC(Pin(if_pin))  # Pico reads 0-3.3V natively
        
        # For motion pin (if wired)
        try:
            self.motion_pin = Pin(motion_pin, Pin.IN)
            self.has_motion_pin = True
        except:
            self.motion_pin = None
            self.has_motion_pin = False
        
        # Statistics
        self.readings = []
        self.max_readings = 100
        self.motion_detected = False
        self.motion_threshold = 100  # ADC threshold for motion
    
    def read_if_signal(self):
        """Read raw IF (intermediate frequency) signal from ADC
        
        Returns:
            dict with signal data
        """
        # Read analog IF output
        if_raw = self.if_adc.read_u16()  # 16-bit ADC (0-65535)
        if_voltage = (if_raw / 65535) * 3.3  # Convert to volts
        
        # Store in history
        self.readings.append(if_raw)
        if len(self.readings) > self.max_readings:
            self.readings.pop(0)
        
        # Calculate motion from IF signal variation
        if len(self.readings) >= 5:
            # Motion is detected as variation in IF signal
            variation = max(self.readings[-5:]) - min(self.readings[-5:])
            self.motion_detected = variation > self.motion_threshold
        
        return {
            'raw': if_raw,
            'voltage': if_voltage,
            'variation': self._calculate_variation()
        }
    
    def read_motion_pin(self):
        """Read digital motion detection pin (if available)
        
        Returns:
            1 if motion detected, 0 if no motion
        """
        if self.has_motion_pin:
            return self.motion_pin.value()
        return None
    
    def _calculate_variation(self):
        """Calculate signal variation (motion indicator)
        
        Returns:
            Variation magnitude (0-65535 scale)
        """
        if len(self.readings) < 2:
            return 0
        return max(self.readings[-10:]) - min(self.readings[-10:])
    
    def estimate_doppler_shift(self):
        """Estimate Doppler shift from IF signal
        
        The HB100 outputs an IF signal. The frequency indicates motion speed.
        Higher frequency = faster motion approaching
        Lower frequency = slower motion or receding
        
        Returns:
            dict with Doppler estimation
        """
        # Crude frequency estimation from signal variation
        variation = self._calculate_variation()
        
        # Rough correlation: variation indicates motion intensity
        # Not true frequency but gives motion presence/intensity
        intensity = min(100, (variation / 65535) * 100)
        
        # Determine direction (approaching/receding) based on IF trend
        if len(self.readings) >= 20:
            recent = sum(self.readings[-10:]) / 10
            older = sum(self.readings[-20:-10]) / 10
            
            if recent > older:
                direction = "Approaching"
            elif recent < older:
                direction = "Receding"
            else:
                direction = "Stationary"
        else:
            direction = "Unknown"
        
        return {
            'intensity': intensity,  # 0-100%
            'direction': direction,
            'variation': variation
        }

# Initialize sensor
sensor = HB100Sensor(if_pin=IF_PIN, motion_pin=MOTION_PIN)

print("Sensor initialized. Reading HB100 output...")
print()

# ============================================================
# TEST FUNCTIONS
# ============================================================

def display_sensor_reading(reading, doppler, motion):
    """Pretty print sensor reading
    
    Args:
        reading: dict from read_if_signal()
        doppler: dict from estimate_doppler_shift()
        motion: digital motion pin reading (or None)
    """
    print("=" * 70)
    print("HB100 SENSOR READING")
    print("=" * 70)
    
    # IF Signal
    print(f"\nIF (Intermediate Frequency) Signal:")
    print(f"  Raw ADC Value:     {reading['raw']:5d} / 65535 (0x{reading['raw']:04x})")
    print(f"  Voltage:           {reading['voltage']:.3f}V")
    print(f"  Signal Variation:  {reading['variation']:5d} (motion indicator)")
    
    # Motion Detection
    print(f"\nMotion Detection:")
    print(f"  Doppler Direction: {doppler['direction']}")
    print(f"  Motion Intensity:  {doppler['intensity']:.1f}%")
    
    if motion is not None:
        motion_status = "DETECTED" if motion == 1 else "Not detected"
        print(f"  Motion Pin:        {motion_status}")
    
    print()

def run_continuous_test(duration_sec=None):
    """Run continuous sensor monitoring
    
    Args:
        duration_sec: How long to monitor (seconds). None = infinite loop
    """
    if duration_sec:
        print(f"CONTINUOUS TEST - Monitoring for {duration_sec} seconds")
    else:
        print("CONTINUOUS LOOP - Monitoring until Ctrl+C (infinite)")
    
    print("Move around the sensor to see motion detection...")
    print("-" * 70)
    
    start_time = utime.time() if duration_sec else None
    sample_count = 0
    motion_count = 0
    
    try:
        while True:
            # Check if time limit reached (if set)
            if duration_sec and utime.time() - start_time > duration_sec:
                break
            
            # Read sensor
            reading = sensor.read_if_signal()
            doppler = sensor.estimate_doppler_shift()
            motion = sensor.read_motion_pin()
            
            sample_count += 1
            if doppler['intensity'] > 10:
                motion_count += 1
            
            # Print concise status every second (10 samples at 100Hz)
            if sample_count % 10 == 0:
                elapsed = utime.time() - start_time if start_time else utime.time()
                print(f"[{elapsed:7.1f}s] ADC:{reading['raw']:5d} " +
                      f"Var:{reading['variation']:5d} " +
                      f"Intensity:{doppler['intensity']:5.1f}% " +
                      f"Direction:{doppler['direction']:<12} " +
                      f"Detected:{motion_count}/{sample_count}")
            
            # Blink LED if motion detected
            if doppler['intensity'] > 20:
                led.on()
            else:
                led.off()
            
            # Sample at ~100Hz
            utime.sleep_ms(10)
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    
    print("-" * 70)
    print(f"Summary: {sample_count} samples, {motion_count} with motion detected")
    print()

def run_single_sample_test():
    """Display single sensor reading
    """
    print("SINGLE SAMPLE TEST")
    print("-" * 70)
    
    for i in range(5):
        reading = sensor.read_if_signal()
        doppler = sensor.estimate_doppler_shift()
        motion = sensor.read_motion_pin()
        
        print(f"Sample {i+1}:")
        print(f"  Raw ADC: {reading['raw']:5d}  Variation: {reading['variation']:5d}  " +
              f"Intensity: {doppler['intensity']:5.1f}%  Direction: {doppler['direction']}")
        
        utime.sleep_ms(100)
    
    print()

def run_raw_adc_stream(duration_sec=10):
    """Stream raw ADC values for analysis
    
    Args:
        duration_sec: How long to stream (seconds)
    """
    print(f"RAW ADC STREAM - {duration_sec} seconds")
    print("Copy this output to analyze signal patterns")
    print("-" * 70)
    
    start_time = utime.time()
    
    # Header for CSV
    print("Time(ms), ADC_Raw, Voltage(V)")
    
    while utime.time() - start_time < duration_sec:
        raw_adc = sensor.if_adc.read_u16()
        voltage = (raw_adc / 65535) * 3.3
        elapsed_ms = int((utime.time() - start_time) * 1000)
        
        print(f"{elapsed_ms}, {raw_adc}, {voltage:.3f}")
        
        utime.sleep_ms(10)
    
    print("-" * 70)
    print()

# ============================================================
# MENU SYSTEM
# ============================================================

def show_menu():
    """Display test menu"""
    print("\nHB100 TEST MENU")
    print("-" * 70)
    print("1. Single Sample Test       - Read 5 sensor samples")
    print("2. Raw ADC Stream          - Stream raw ADC values for analysis")
    print("3. Continuous Test (30s)   - Monitor sensor for 30 seconds")
    print("4. Infinite Loop Monitor    - Monitor forever (Ctrl+C to stop)")
    print("5. Sensitivity Test        - Find motion threshold")
    print("6. Calibration             - Record baseline readings")
    print("7. Exit                    - Exit test")
    print("-" * 70)

def run_sensitivity_test():
    """Find the motion detection threshold"""
    print("SENSITIVITY TEST - Wave your hand over the sensor")
    print("-" * 70)
    print("No Motion Baseline:")
    
    # Record baseline (no motion)
    baseline_readings = []
    print("  Hold still for 3 seconds...")
    start = utime.time()
    while utime.time() - start < 3:
        raw = sensor.if_adc.read_u16()
        baseline_readings.append(raw)
        utime.sleep_ms(10)
    
    baseline_avg = sum(baseline_readings) / len(baseline_readings)
    baseline_var = max(baseline_readings) - min(baseline_readings)
    
    print(f"  Average:  {baseline_avg:.0f}")
    print(f"  Variation: {baseline_var}")
    
    print("\nWith Motion Detected:")
    print("  Move your hand over sensor for 3 seconds...")
    motion_readings = []
    start = utime.time()
    while utime.time() - start < 3:
        raw = sensor.if_adc.read_u16()
        motion_readings.append(raw)
        utime.sleep_ms(10)
    
    motion_avg = sum(motion_readings) / len(motion_readings)
    motion_var = max(motion_readings) - min(motion_readings)
    
    print(f"  Average:   {motion_avg:.0f}")
    print(f"  Variation:  {motion_var}")
    
    print("\nThreshold Recommendation:")
    print(f"  Current setting: {sensor.motion_threshold}")
    suggested = motion_var - baseline_var
    print(f"  Suggested: {suggested}")
    print()

def run_calibration():
    """Record baseline readings"""
    print("CALIBRATION - Recording baseline (no motion for 10 seconds)")
    print("-" * 70)
    
    readings = []
    for i in range(100):
        raw = sensor.if_adc.read_u16()
        readings.append(raw)
        if i % 10 == 0:
            print(f"  Reading {i}: {raw}")
        utime.sleep_ms(100)
    
    avg = sum(readings) / len(readings)
    min_val = min(readings)
    max_val = max(readings)
    variation = max_val - min_val
    
    print("\nCalibration Results:")
    print(f"  Samples:   {len(readings)}")
    print(f"  Average:   {avg:.0f}")
    print(f"  Min:       {min_val}")
    print(f"  Max:       {max_val}")
    print(f"  Variation: {variation}")
    print()

# ============================================================
# MAIN TEST LOOP
# ============================================================

try:
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect test (1-7): ").strip()
            
            if choice == "1":
                run_single_sample_test()
            elif choice == "2":
                run_raw_adc_stream()
            elif choice == "3":
                run_continuous_test(30)
            elif choice == "4":
                print("\n" + "="*70)
                print("INFINITE LOOP MODE - Press Ctrl+C to return to menu")
                print("="*70 + "\n")
                run_continuous_test(duration_sec=None)  # None = infinite
            elif choice == "5":
                run_sensitivity_test()
            elif choice == "6":
                run_calibration()
            elif choice == "7":
                print("\nExiting test...")
                break
            else:
                print("Invalid choice. Please select 1-7.")
        
        except KeyboardInterrupt:
            print("\n(Returning to menu)")
        except Exception as e:
            print(f"Error: {e}")

except KeyboardInterrupt:
    print("\n\nTest terminated by user")

finally:
    led.off()
    print("HB100 test complete!")
