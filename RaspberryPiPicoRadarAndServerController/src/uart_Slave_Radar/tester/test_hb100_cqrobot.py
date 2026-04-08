# HB100 Doppler Radar - CQRobot Module Tester
# MicroPython test script for Raspberry Pi Pico
# Tests CQRobot HB100 10.525GHz module (SKU: CQRSENWB01)
# Includes motion pin detection and optimized CQRobot configuration

from machine import ADC, Pin, PWM, Timer
import utime

print("=" * 70)
print("HB100 DOPPLER RADAR - CQROBOT MODULE TEST")
print("CQRobot 10.525GHz Microwave Motion Detection Module")
print("SKU: CQRSENWB01")
print("=" * 70)
print()

# ============================================================
# CQROBOT PINOUT
# ============================================================
# Standard CQRobot module connections

# CQRobot IF Output (Analog - for continuous signal reading)
IF_PIN = 27                 # ADC1 on Pico (GPIO27)
IF_ADC = ADC(Pin(IF_PIN))   # Analog intermediate frequency output

# CQRobot Motion Detection Pin (Digital - motion detected -> HIGH)
MOTION_PIN = 26             # GPIO26 - Digital input
motion_pin = Pin(MOTION_PIN, Pin.IN)

# Status LED
led = Pin("LED", Pin.OUT)
led.on()

print("CQRobot Module Pinout:")
print("  CQRobot GND:       GND on Pico")
print("  CQRobot VCC:       3.3V on Pico")
print("  CQRobot IF OUT:    GPIO{} (ADC1)".format(IF_PIN))
print("  CQRobot MOTION:    GPIO{} (Digital IN)".format(MOTION_PIN))
print()
print("CQRobot Features:")
print("  • Dual output: Analog IF + Digital Motion")
print("  • Built-in amplification")
print("  • 5GHz-15GHz frequency range (centered ~10.525GHz)")
print("  • Pre-tuned for motion detection")
print("=" * 70)
print()

# ============================================================
# CQROBOT SENSOR CLASS
# ============================================================

class HB100CQRobot:
    """CQRobot HB100 Module Reader with IF and Motion detection"""
    
    def __init__(self, if_pin=27, motion_pin=26):
        """Initialize CQRobot module
        
        Args:
            if_pin: ADC pin for IF output
            motion_pin: Digital pin for motion detection
        """
        # IF reading
        self.if_adc = ADC(Pin(if_pin))  # Pico reads 0-3.3V natively
        
        # Motion detection
        self.motion_digital = Pin(motion_pin, Pin.IN)
        
        # Statistics
        self.if_readings = []
        self.max_readings = 100
        self.motion_events = 0
        self.motion_threshold = 100  # ADC variation threshold
    
    def read_if(self):
        """Read analog IF output
        
        Returns:
            dict with IF signal data
        """
        raw = self.if_adc.read_u16()
        self.if_readings.append(raw)
        if len(self.if_readings) > self.max_readings:
            self.if_readings.pop(0)
        
        return {
            'raw': raw,
            'voltage': (raw / 65535) * 3.3,
            'variation': self._get_variation()
        }
    
    def read_motion_pin(self):
        """Read CQRobot motion detection pin
        
        Returns:
            1 if motion detected, 0 if no motion
        """
        state = self.motion_digital.value()
        if state == 1:
            self.motion_events += 1
        return state
    
    def read_combined(self):
        """Read both IF and motion pin together
        
        Returns:
            dict with all sensor data
        """
        if_data = self.read_if()
        motion = self.read_motion_pin()
        
        return {
            'timestamp': utime.time(),
            'if_raw': if_data['raw'],
            'if_voltage': if_data['voltage'],
            'if_variation': if_data['variation'],
            'motion_pin': motion,
            'motion_detected': motion == 1,
            'motion_intensity': self._estimate_intensity()
        }
    
    def _get_variation(self):
        """Get IF signal variation (motion indicator)"""
        if len(self.if_readings) < 2:
            return 0
        return max(self.if_readings[-20:]) - min(self.if_readings[-20:])
    
    def _estimate_intensity(self):
        """Estimate motion intensity from IF and digital combined
        
        Returns:
            0-100 representing motion intensity
        """
        # Pin reading: strong indicator (0 or 100)
        pin_state = self.motion_digital.value()
        if pin_state == 1:
            pin_value = 100
        else:
            pin_value = 0
        
        # IF variation: secondary indicator
        if_var = self._get_variation()
        if_intensity = min(100, (if_var / 65535) * 100)
        
        # Combine: weight pin detection heavily
        combined = (pin_value * 0.7) + (if_intensity * 0.3)
        return combined

# Initialize sensor
sensor = HB100CQRobot(if_pin=IF_PIN, motion_pin=MOTION_PIN)

print("CQRobot module initialized.")
print("Dual sensing: IF (analog) + MOTION (digital)")
print()

# ============================================================
# TEST FUNCTIONS
# ============================================================

def display_reading(data):
    """Pretty print sensor reading"""
    print("\nCQROBOT SENSOR READING:")
    print("-" * 70)
    print(f"Time:              {data['timestamp']:.2f}")
    print(f"\nAnalog IF Output:")
    print(f"  Raw ADC:         {data['if_raw']:5d} / 65535 (0x{data['if_raw']:04x})")
    print(f"  Voltage:         {data['if_voltage']:.3f}V")
    print(f"  Variation:       {data['if_variation']:5d}")
    print(f"\nDigital Motion Pin:")
    print(f"  State:           {data['motion_pin']} ({'Detected' if data['motion_detected'] else 'No motion'})")
    print(f"  Events:          {sensor.motion_events}")
    print(f"  Intensity:       {data['motion_intensity']:.1f}%")
    print()

def run_single_sample():
    """Display single reading"""
    print("SINGLE SAMPLE TEST - CQRobot Output")
    print("-" * 70)
    
    for i in range(5):
        data = sensor.read_combined()
        print(f"Sample {i+1}:")
        print(f"  IF: {data['if_raw']:5d}  Motion Pin: {data['motion_pin']}  " +
              f"Intensity: {data['motion_intensity']:5.1f}%")
        utime.sleep_ms(100)
    
    print()

def run_dual_monitor(duration_sec=None):
    """Monitor both IF and motion pin
    
    Args:
        duration_sec: Duration (None = infinite)
    """
    if duration_sec:
        mode_str = f"for {duration_sec} seconds"
    else:
        mode_str = "infinitely"
    
    print(f"DUAL MONITOR - IF + Motion Pin {mode_str}")
    print("Move hand over sensor to trigger motion detection...")
    print("-" * 70)
    
    start_time = utime.time() if duration_sec else None
    samples = 0
    motion_samples = 0
    
    try:
        while True:
            if duration_sec and utime.time() - start_time > duration_sec:
                break
            
            data = sensor.read_combined()
            samples += 1
            if data['motion_detected']:
                motion_samples += 1
            
            # Print every 10 samples
            if samples % 10 == 0:
                elapsed = utime.time() - (start_time if start_time else utime.time())
                motion_str = "YES" if data['motion_detected'] else "NO "
                print(f"[{elapsed:7.1f}s] IF:{data['if_raw']:5d} " +
                      f"Motion:{motion_str} Intensity:{data['motion_intensity']:5.1f}%")
            
            # LED indicator
            if data['motion_detected']:
                led.on()
            else:
                led.off()
            
            utime.sleep_ms(50)  # ~20Hz for motion pin responsiveness
    
    except KeyboardInterrupt:
        print("\nMonitoring stopped")
    
    print("-" * 70)
    print(f"Summary: {samples} samples, {motion_samples} motion detections")
    print()

def run_motion_pin_test():
    """Dedicated motion pin polling test"""
    print("MOTION PIN TEST - Digital Motion Detection Only")
    print("Optimized for quick motion response (~20Hz polling)")
    print("-" * 70)
    
    print("Test duration: 30 seconds")
    print("Move slowly and quickly to see response time...")
    
    start = utime.time()
    samples = 0
    motion_count = 0
    motion_change_events = 0
    last_state = 0
    
    try:
        while utime.time() - start < 30:
            current_state = sensor.read_motion_pin()
            
            # Count state changes
            if current_state != last_state:
                motion_change_events += 1
                last_state = current_state
                state_str = "MOTION DETECTED!" if current_state == 1 else "No motion"
                elapsed = utime.time() - start
                print(f"  [{elapsed:.1f}s] {state_str}")
            
            if current_state == 1:
                motion_count += 1
            
            samples += 1
            utime.sleep_ms(50)  # 20Hz polling
    
    except KeyboardInterrupt:
        print("\nTest stopped")
    
    print("-" * 70)
    print(f"Results:")
    print(f"  Total samples: {samples}")
    print(f"  Motion detected: {motion_count} samples")
    print(f"  State changes: {motion_change_events}")
    print(f"  Motion percentage: {(motion_count/samples)*100:.1f}%")
    print()

def run_if_stream():
    """Stream IF signal values (motion pin ignored)"""
    print("IF STREAM TEST - Analog Signal Only (CSV)")
    print("Captures 20 seconds of IF signal for analysis")
    print("-" * 70)
    print("Time_s, IF_Raw, IF_Voltage, IF_Variation")
    
    start = utime.time()
    
    try:
        while utime.time() - start < 20:
            data = sensor.read_if()
            elapsed = utime.time() - start
            
            print(f"{elapsed:.2f}, {data['raw']}, {data['voltage']:.3f}, {data['variation']}")
            
            utime.sleep_ms(10)
    
    except KeyboardInterrupt:
        print("Stream stopped")
    
    print("-" * 70)
    print()

def run_sensitivity_test():
    """Measure motion pin response threshold"""
    print("MOTION PIN SENSITIVITY TEST")
    print("-" * 70)
    
    print("Step 1: STATIONARY - Hold sensor still for 5 seconds...")
    stationary_time = 0
    start = utime.time()
    while utime.time() - start < 5:
        if sensor.read_motion_pin() == 1:
            stationary_time += 1
        utime.sleep_ms(50)
    
    print(f"  Motion pin HIGH: {stationary_time} / 100 samples")
    
    print("\nStep 2: SLOW MOTION - Slowly wave hand over sensor for 5 seconds...")
    slow_motion_time = 0
    start = utime.time()
    while utime.time() - start < 5:
        if sensor.read_motion_pin() == 1:
            slow_motion_time += 1
        utime.sleep_ms(50)
    
    print(f"  Motion pin HIGH: {slow_motion_time} / 100 samples")
    
    print("\nStep 3: FAST MOTION - Quickly move hand over sensor for 5 seconds...")
    fast_motion_time = 0
    start = utime.time()
    while utime.time() - start < 5:
        if sensor.read_motion_pin() == 1:
            fast_motion_time += 1
        utime.sleep_ms(50)
    
    print(f"  Motion pin HIGH: {fast_motion_time} / 100 samples")
    
    print("\nSensitivity Analysis:")
    print(f"  Stationary: {stationary_time}% motion detection (baseline)")
    print(f"  Slow: {slow_motion_time}% motion detection")
    print(f"  Fast: {fast_motion_time}% motion detection")
    print(f"  Sensitivity: {'Good' if fast_motion_time > 70 else 'May need adjustment'}")
    print()

def run_correlation_test():
    """Compare IF signal vs motion pin"""
    print("CORRELATION TEST - IF vs Motion Pin")
    print("Measures how well IF signal and motion pin agree")
    print("-" * 70)
    
    print("Collecting 10 seconds of dual data...")
    
    start = utime.time()
    if_high = 0
    pin_high = 0
    both_high = 0
    if_alone = 0
    pin_alone = 0
    
    samples = 0
    
    try:
        while utime.time() - start < 10:
            data = sensor.read_combined()
            
            if_var = data['if_variation']
            pin_state = data['motion_pin']
            
            if_active = if_var > 100  # Threshold
            pin_active = pin_state == 1
            
            if if_active:
                if_high += 1
            if pin_active:
                pin_high += 1
            if if_active and pin_active:
                both_high += 1
            elif if_active and not pin_active:
                if_alone += 1
            elif not if_active and pin_active:
                pin_alone += 1
            
            samples += 1
            utime.sleep_ms(50)
    
    except KeyboardInterrupt:
        print("Test stopped")
    
    print("-" * 70)
    print(f"Results (out of {samples} samples):")
    print(f"  IF active: {if_high} ({(if_high/samples)*100:.1f}%)")
    print(f"  Pin active: {pin_high} ({(pin_high/samples)*100:.1f}%)")
    print(f"  Both active: {both_high} ({(both_high/samples)*100:.1f}%)")
    print(f"  IF only: {if_alone} ({(if_alone/samples)*100:.1f}%)")
    print(f"  Pin only: {pin_alone} ({(pin_alone/samples)*100:.1f}%)")
    print(f"  Correlation: {'Strong' if both_high > samples*0.7 else 'Weak'}")
    print()

# ============================================================
# MENU SYSTEM
# ============================================================

def show_menu():
    """Display test menu"""
    print("\nCQROBOT MODULE TEST MENU")
    print("-" * 70)
    print("1. Single Sample          - Read 5 sensor samples")
    print("2. Dual Monitor (30s)     - Monitor IF + Motion pin")
    print("3. Infinite Dual Monitor  - Monitor forever (Ctrl+C to stop)")
    print("4. Motion Pin Test        - Digital motion detection only")
    print("5. IF Stream              - Raw IF signal (20s CSV)")
    print("6. Sensitivity Test       - Motion pin response threshold")
    print("7. Correlation Test       - IF vs Motion pin agreement")
    print("8. Exit                   - Exit test")
    print("-" * 70)

# ============================================================
# MAIN LOOP
# ============================================================

try:
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect test (1-8): ").strip()
            
            if choice == "1":
                run_single_sample()
            elif choice == "2":
                run_dual_monitor(30)
            elif choice == "3":
                print("\n" + "="*70)
                print("INFINITE DUAL MONITOR - Press Ctrl+C to return to menu")
                print("="*70 + "\n")
                run_dual_monitor(None)
            elif choice == "4":
                run_motion_pin_test()
            elif choice == "5":
                run_if_stream()
            elif choice == "6":
                run_sensitivity_test()
            elif choice == "7":
                run_correlation_test()
            elif choice == "8":
                print("\nExiting test...")
                break
            else:
                print("Invalid choice. Please select 1-8.")
        
        except KeyboardInterrupt:
            print("\n(Returning to menu)")
        except Exception as e:
            print(f"Error: {e}")

except KeyboardInterrupt:
    print("\n\nTest terminated by user")

finally:
    led.off()
    print("CQRobot test complete!")
