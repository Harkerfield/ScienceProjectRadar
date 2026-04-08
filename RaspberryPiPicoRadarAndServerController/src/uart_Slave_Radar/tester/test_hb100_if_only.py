# HB100 Doppler Radar - IF Only (Raw ADC) Tester
# MicroPython test script for Raspberry Pi Pico
# Tests raw IF (Intermediate Frequency) output from HB100 sensor
# Reads analog IF output directly via ADC pin

from machine import ADC, Pin, Timer
import utime
import math

print("=" * 70)
print("HB100 DOPPLER RADAR - IF ONLY (RAW ADC) TEST")
print("10.525GHz Microwave Motion Sensor")
print("=" * 70)
print()

# ============================================================
# IF-ONLY CONFIGURATION
# ============================================================
# For raw IF output - connect directly to any ADC-capable GPIO

IF_PIN = 27                 # ADC1 on Pico (GPIO27) - CONFIGURABLE
IF_ADC = ADC(Pin(IF_PIN))   # Analog intermediate frequency output

# LED indicator
led = Pin("LED", Pin.OUT)
led.on()

print("HB100 IF-Only Configuration:")
print(f"  IF Output Pin:     GPIO{IF_PIN} (ADC)")
print(f"  Status LED:        GPIO25")
print()
print("Connections (Flexible):")
print("  HB100 VCC:         3.3V on Pico")
print("  HB100 GND:         GND on Pico")
print("  HB100 IF Output:   GPIO{} (any ADC pin)".format(IF_PIN))
print()
print("ADC-Capable GPIO Pins on Pico:")
print("  GPIO26-29:         ADC0-3 (Recommended)")
print("=" * 70)
print()

# ============================================================
# IF SENSOR CLASS
# ============================================================

class HB100IFSensor:
    """HB100 Raw IF Signal Reader - Direct ADC monitoring"""
    
    def __init__(self, if_pin=27):
        """Initialize IF sensor
        
        Args:
            if_pin: GPIO pin connected to IF output (must be ADC-capable)
        """
        self.if_adc = ADC(Pin(if_pin))  # Pico reads 0-3.3V natively
        
        # Statistics
        self.readings = []
        self.max_readings = 100
    
    def read_raw_adc(self):
        """Read raw ADC value
        
        Returns:
            16-bit ADC value (0-65535)
        """
        raw = self.if_adc.read_u16()
        self.readings.append(raw)
        if len(self.readings) > self.max_readings:
            self.readings.pop(0)
        return raw
    
    def read_voltage(self):
        """Read IF output as voltage
        
        Returns:
            Voltage value (0.0-3.3V)
        """
        raw = self.read_raw_adc()
        return (raw / 65535) * 3.3
    
    def read_with_stats(self):
        """Read ADC with analysis
        
        Returns:
            dict with raw, voltage, and variation data
        """
        raw = self.read_raw_adc()
        voltage = (raw / 65535) * 3.3
        
        # Calculate variation (motion indicator)
        if len(self.readings) >= 2:
            variation = max(self.readings[-10:]) - min(self.readings[-10:])
        else:
            variation = 0
        
        return {
            'raw': raw,
            'voltage': voltage,
            'variation': variation,
            'timestamp': utime.time()
        }
    
    def get_motion_intensity(self):
        """Estimate motion intensity from IF variation
        
        Returns:
            Percentage 0-100% indicating motion presence
        """
        if len(self.readings) < 2:
            return 0.0
        
        variation = max(self.readings[-20:]) - min(self.readings[-20:])
        intensity = min(100, (variation / 65535) * 100)
        return intensity
    
    def get_motion_trend(self):
        """Determine if motion is increasing or decreasing
        
        Returns:
            "Approaching", "Receding", or "Stationary"
        """
        if len(self.readings) < 20:
            return "Unknown"
        
        recent = sum(self.readings[-10:]) / 10
        older = sum(self.readings[-20:-10]) / 10
        
        if abs(recent - older) < 100:
            return "Stationary"
        elif recent > older:
            return "Approaching"
        else:
            return "Receding"

# Initialize sensor
sensor = HB100IFSensor(if_pin=IF_PIN)

print("IF sensor initialized. Reading HB100 IF output...")
print()

# ============================================================
# TEST FUNCTIONS
# ============================================================

def run_single_sample():
    """Display single IF reading"""
    print("SINGLE SAMPLE TEST - IF Output Reading")
    print("-" * 70)
    
    for i in range(5):
        data = sensor.read_with_stats()
        
        print(f"Sample {i+1}:")
        print(f"  Raw ADC:       {data['raw']:5d} / 65535 (0x{data['raw']:04x})")
        print(f"  Voltage:       {data['voltage']:.3f}V")
        print(f"  Variation:     {data['variation']:5d}")
        
        utime.sleep_ms(100)
    
    print()

def run_continuous_monitor(duration_sec=None):
    """Monitor IF signal continuously
    
    Args:
        duration_sec: Duration in seconds (None = infinite)
    """
    if duration_sec:
        mode_str = f"for {duration_sec} seconds"
    else:
        mode_str = "infinitely"
    
    print(f"CONTINUOUS MONITOR - IF signal {mode_str}")
    print("move hand over sensor to see IF signal changes...")
    print("-" * 70)
    
    start_time = utime.time() if duration_sec else None
    sample_count = 0
    motion_count = 0
    
    try:
        while True:
            if duration_sec and utime.time() - start_time > duration_sec:
                break
            
            data = sensor.read_with_stats()
            intensity = sensor.get_motion_intensity()
            trend = sensor.get_motion_trend()
            
            sample_count += 1
            if intensity > 10:
                motion_count += 1
            
            # Print every 10 samples (~100ms at 100Hz)
            if sample_count % 10 == 0:
                elapsed = utime.time() - (start_time if start_time else utime.time())
                print(f"[{elapsed:7.1f}s] ADC:{data['raw']:5d}V:{data['voltage']:.2f} " +
                      f"Var:{data['variation']:5d} Motion:{intensity:5.1f}% Trend:{trend}")
            
            # Blink LED on motion
            if intensity > 20:
                led.on()
            else:
                led.off()
            
            utime.sleep_ms(10)  # 100Hz sampling
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    
    print("-" * 70)
    print(f"Summary: {sample_count} samples, {motion_count} with motion")
    print()

def run_raw_adc_stream(duration_sec=10):
    """Stream raw ADC values for external analysis
    
    Args:
        duration_sec: Duration to stream
    """
    print(f"RAW ADC STREAM - {duration_sec} seconds (CSV format)")
    print("Capture this output for signal analysis in spreadsheet")
    print("-" * 70)
    print("Time_ms, ADC_Raw, Voltage_V, Variation")
    
    start_time = utime.time()
    
    while utime.time() - start_time < duration_sec:
        data = sensor.read_with_stats()
        elapsed_ms = int((utime.time() - start_time) * 1000)
        
        print(f"{elapsed_ms}, {data['raw']}, {data['voltage']:.3f}, {data['variation']}")
        
        utime.sleep_ms(10)
    
    print("-" * 70)
    print()

def run_sensitivity_calibration():
    """Measure baseline and motion thresholds"""
    print("SENSITIVITY CALIBRATION")
    print("-" * 70)
    
    # Baseline (no motion)
    print("Step 1: BASELINE - Hold sensor still for 3 seconds...")
    baseline = []
    start = utime.time()
    while utime.time() - start < 3:
        baseline.append(sensor.read_raw_adc())
        utime.sleep_ms(10)
    
    baseline_avg = sum(baseline) / len(baseline)
    baseline_var = max(baseline) - min(baseline)
    
    print(f"  Average: {baseline_avg:.0f}")
    print(f"  Variation: {baseline_var}")
    
    # Motion test
    print("\nStep 2: MOTION - Wave hand over sensor for 3 seconds...")
    motion = []
    start = utime.time()
    while utime.time() - start < 3:
        motion.append(sensor.read_raw_adc())
        utime.sleep_ms(10)
    
    motion_avg = sum(motion) / len(motion)
    motion_var = max(motion) - min(motion)
    
    print(f"  Average: {motion_avg:.0f}")
    print(f"  Variation: {motion_var}")
    
    print("\nCalibration Results:")
    print(f"  Baseline variation: {baseline_var}")
    print(f"  Motion variation: {motion_var}")
    print(f"  Difference: {motion_var - baseline_var}")
    print()

def run_frequency_test():
    """Attempt to estimate Doppler frequency from IF variations"""
    print("FREQUENCY ESTIMATION TEST")
    print("Collects samples and estimates Doppler frequency from IF signal")
    print("-" * 70)
    
    print("Reading 200 samples (no motion)...")
    baseline_samples = []
    for i in range(200):
        baseline_samples.append(sensor.read_raw_adc())
        utime.sleep_ms(5)
    
    print("Reading 200 samples (with motion)...")
    motion_samples = []
    print("  Wave hand over sensor...")
    for i in range(200):
        motion_samples.append(sensor.read_raw_adc())
        utime.sleep_ms(5)
    
    # Simple analysis
    baseline_avg = sum(baseline_samples) / len(baseline_samples)
    motion_avg = sum(motion_samples) / len(motion_samples)
    
    # Count zero-crossings as rough frequency indicator
    baseline_crossing = 0
    for i in range(1, len(baseline_samples)):
        if (baseline_samples[i] - baseline_avg) * (baseline_samples[i-1] - baseline_avg) < 0:
            baseline_crossing += 1
    
    motion_crossing = 0
    for i in range(1, len(motion_samples)):
        if (motion_samples[i] - motion_avg) * (motion_samples[i-1] - motion_avg) < 0:
            motion_crossing += 1
    
    print(f"\nResults:")
    print(f"  Baseline zero-crossings: {baseline_crossing}")
    print(f"  Motion zero-crossings: {motion_crossing}")
    print(f"  Frequency indicator: {'Motion Detected' if motion_crossing > baseline_crossing + 2 else 'No motion'}")
    print()

# ============================================================
# MENU SYSTEM
# ============================================================

def show_menu():
    """Display test menu"""
    print("\nHB100 IF-ONLY TEST MENU")
    print("-" * 70)
    print("1. Single Sample         - Read 5 IF samples")
    print("2. Continuous Monitor    - Monitor IF for 30 seconds")
    print("3. Infinite Monitor      - Monitor forever (Ctrl+C to stop)")
    print("4. Raw ADC Stream        - CSV output for analysis")
    print("5. Sensitivity Test      - Calibrate motion threshold")
    print("6. Frequency Test        - Estimate Doppler frequency")
    print("7. Exit                  - Exit test")
    print("-" * 70)

# ============================================================
# MAIN LOOP
# ============================================================

try:
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect test (1-7): ").strip()
            
            if choice == "1":
                run_single_sample()
            elif choice == "2":
                run_continuous_monitor(30)
            elif choice == "3":
                print("\n" + "="*70)
                print("INFINITE MONITOR MODE - Press Ctrl+C to return to menu")
                print("="*70 + "\n")
                run_continuous_monitor(None)
            elif choice == "4":
                run_raw_adc_stream(20)
            elif choice == "5":
                run_sensitivity_calibration()
            elif choice == "6":
                run_frequency_test()
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
    print("IF-Only test complete!")
