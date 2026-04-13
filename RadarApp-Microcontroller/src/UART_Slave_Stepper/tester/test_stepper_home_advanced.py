# Stepper Motor Home Finding Tester - Step 2
# Rotates motor to find home position with variable speeds
from machine import Pin
import utime

print("=" * 60)
print("stepper MOTOR home FINDING - Step 2")
print("=" * 60)
print()

# ============================================================
# STATIC CONFIGURATION VARIABLES
# ============================================================

# Motor pins
PUL_PIN = 5              # Pulse pin
DIR_PIN = 6              # Direction pin
ENA_PIN = 7              # Enable pin

# Sensor pin
SENSOR_PIN = 20          # Inductive home sensor (active LOW)

# Motor configuration
STEPS_PER_REVOLUTION = 600  # With gear reduction (3:1)
DEGREES_PER_STEP = 0.6      # 360 / 600

# Speed configuration (in microseconds for pulse duration)
INITIAL_speed_US = 500      # Initial rotation speed (500µs per pulse)
FINE_speed_US = 1000        # Fine-tuning speed very slow (1000µs per pulse)

# Direction definitions
CW = 1
CCW = 0

# ============================================================
# PIN INITIALIZATION
# ============================================================

pul_pin = Pin(PUL_PIN, Pin.OUT)
dir_pin = Pin(DIR_PIN, Pin.OUT)
ena_pin = Pin(ENA_PIN, Pin.OUT)
sensor_pin = Pin(SENSOR_PIN, Pin.IN, Pin.PULL_UP)
led_pin = Pin("LED", Pin.OUT)

# Set initial safe state
ena_pin.on()  # Motor disabled
pul_pin.off()
dir_pin.on()  # CW

print("✓ Pins initialized")
print()
print("Configuration:")
print(f"  Initial speed: {INITIAL_speed_US}µs")
print(f"  Fine-tuning speed: {FINE_speed_US}µs")
print(f"  Sensor pin: GPIO {SENSOR_PIN}")
print()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def pulse_motor(speed_us):
    """
    Send a single pulse to stepper motor
    
    Args:
        speed_us: Pulse duration in microseconds (higher = slower)
    """
    pul_pin.on()
    utime.sleep_us(speed_us)
    pul_pin.off()
    utime.sleep_us(speed_us)

def enable_motor():
    """Enable stepper motor"""
    ena_pin.off()
    print("  ✓ Motor enabled")

def disable_motor():
    """Disable stepper motor"""
    ena_pin.on()
    print("  ✓ Motor disabled")

def set_direction(direction):
    """
    Set motor direction
    
    Args:
        direction: CW (1) or CCW (0)
    """
    dir_pin.value(direction)
    dir_label = "CW" if direction == CW else "CCW"
    print(f"  ✓ Direction set to {dir_label}")

def get_sensor_state():
    """
    Read sensor state
    
    Returns:
        1 = metal detected (home triggered)
        0 = clear
    """
    return sensor_pin.value()

def rotate_to_home(direction):
    """
    Rotate motor until sensor triggers (home position found)
    
    Args:
        direction: CW (1) or CCW (0) - direction to search for home
        
    Returns:
        Number of steps taken to find home, or -1 if not found
    """
    print()
    print("=" * 60)
    print("[PHASE 1] ROTATING TO home")
    print("=" * 60)
    
    dir_label = "CW" if direction == CW else "CCW"
    print(f"Direction: {dir_label}")
    print(f"Speed: {INITIAL_speed_US}µs per pulse")
    print()
    
    # Set direction
    set_direction(direction)
    enable_motor()
    
    # Check initial sensor state
    initial_sensor = get_sensor_state()
    print(f"Initial sensor state: {initial_sensor} (1=home, 0=CLEAR)")
    
    # If already at home, move away first
    if initial_sensor == 1:
        print()
        print("Sensor already triggered! Moving away first...")
        dir_opposite = CCW if direction == CW else CW
        set_direction(dir_opposite)
        
        # Move away until sensor clears
        away_steps = 0
        max_away = STEPS_PER_REVOLUTION * 2
        
        while away_steps < max_away:
            pulse_motor(INITIAL_speed_US)
            away_steps += 1
            
            if get_sensor_state() == 0:  # Sensor cleared
                print(f"  ✓ Cleared after {away_steps} steps")
                break
            
            if away_steps % 100 == 0:
                print(f"  Moving... {away_steps} steps", end="\r")
        
        if away_steps == max_away:
            print(f"  ✗ Could not clear sensor!")
            disable_motor()
            return -1
        
        # Reset direction back to original search direction
        print()
        set_direction(direction)
        utime.sleep_ms(100)
    
    print()
    print("Searching for home sensor...")
    
    # Rotate until sensor triggers
    steps = 0
    max_steps = STEPS_PER_REVOLUTION * 5  # Allow 5 revolutions max
    
    while steps < max_steps:
        pulse_motor(INITIAL_speed_US)
        steps += 1
        
        if get_sensor_state() == 1:  # Home found!
            print(f"\n✓ home TRIGGERED!")
            angle = steps * DEGREES_PER_STEP
            print(f"  Triggered at: {steps} steps ({angle:.1f}°)")
            disable_motor()
            led_pin.on()
            utime.sleep_ms(500)
            led_pin.off()
            return steps
        
        # Progress update every 100 steps
        if steps % 100 == 0:
            revolutions = steps / STEPS_PER_REVOLUTION
            angle = (steps % STEPS_PER_REVOLUTION) * DEGREES_PER_STEP
            print(f"  Progress: {revolutions:.1f}R + {angle:.1f}°", end="\r")
    
    print(f"\n✗ home NOT FOUND after {max_steps} steps!")
    disable_motor()
    return -1

def reverse_and_fine_tune(initial_direction, home_steps):
    """
    Reverse direction and slowly approach home
    
    Args:
        initial_direction: Direction we just came from (CW or CCW)
        home_steps: Number of steps from search start to home
        
    Returns:
        Total distance traveled back toward home
    """
    print()
    print("=" * 60)
    print("[PHASE 2] REVERSE & FINE-TUNE APPROACH")
    print("=" * 60)
    print()
    
    # Reverse direction
    reverse_direction = CCW if initial_direction == CW else CW
    dir_label = "CW" if reverse_direction == CW else "CCW"
    print(f"Reversing direction: {dir_label}")
    print(f"Speed: {FINE_speed_US}µs per pulse (very slow)")
    print()
    
    set_direction(reverse_direction)
    enable_motor()
    
    print("Moving back toward home slowly...")
    
    # Move back until sensor triggers again
    steps = 0
    
    while steps < home_steps + 100:  # Allow some overshoot
        pulse_motor(FINE_speed_US)
        steps += 1
        
        if get_sensor_state() == 1:  # Home triggered!
            print(f"\n✓ home RE-TRIGGERED!")
            print(f"  Returned to home after: {steps} steps")
            disable_motor()
            led_pin.on()
            utime.sleep_ms(300)
            led_pin.off()
            utime.sleep_ms(200)
            led_pin.on()
            utime.sleep_ms(300)
            led_pin.off()
            return steps
        
        # Progress update every 50 steps
        if steps % 50 == 0:
            print(f"  Approaching... {steps} steps", end="\r")
    
    print(f"\n✗ DID NOT RE-TRIGGER after {steps} steps!")
    disable_motor()
    return -1

def rotate_then_go_home():
    """
    Rotate motor by specified amount, then return to home
    """
    print()
    print("=" * 60)
    print("[CUSTOM] rotate & GO home")
    print("=" * 60)
    print()
    
    print("How many degrees to rotate?")
    print("Enter degrees (1-360): ", end="")
    
    try:
        degrees = float(input().strip())
        
        if degrees < 1 or degrees > 360:
            print("✗ Invalid range (1-360)")
            return
        
        # Calculate steps needed
        steps_needed = int(degrees / DEGREES_PER_STEP)
        
        print()
        print("Select rotation direction:")
        print("1. Clockwise (CW)")
        print("2. Counter-Clockwise (CCW)")
        print()
        print("Enter choice (1-2): ", end="")
        
        dir_choice = input().strip()
        
        if dir_choice == "1":
            rotation_dir = CW
            dir_label = "CW"
        elif dir_choice == "2":
            rotation_dir = CCW
            dir_label = "CCW"
        else:
            print("✗ Invalid choice")
            return
        
        print()
        print("=" * 60)
        print(f"Rotating {degrees}° {dir_label} then returning to home")
        print("=" * 60)
        print()
        
        # Phase 1: Rotate specified amount
        print("[PHASE 1] ROTATING")
        print(f"Target: {degrees}° ({steps_needed} steps)")
        print(f"Speed: {INITIAL_speed_US}µs per pulse")
        print()
        
        set_direction(rotation_dir)
        enable_motor()
        
        for step in range(steps_needed):
            pulse_motor(INITIAL_speed_US)
            
            if (step + 1) % 100 == 0:
                current_angle = (step + 1) * DEGREES_PER_STEP
                print(f"  Rotated: {current_angle:.1f}°", end="\r")
        
        print(f"\n  ✓ Rotation complete: {degrees}°")
        disable_motor()
        
        # Pause between phases
        print()
        print("Pausing 1 second...")
        utime.sleep(1)
        
        # Phase 2: Return to home
        print()
        print("[PHASE 2] RETURNING TO home")
        print(f"Speed: {FINE_speed_US}µs per pulse (very slow)")
        print()
        
        # Reverse direction
        home_direction = CCW if rotation_dir == CW else CW
        home_dir_label = "CW" if home_direction == CW else "CCW"
        print(f"Direction: {home_dir_label}")
        
        set_direction(home_direction)
        enable_motor()
        
        print("Slowly approaching home...")
        
        home_steps = 0
        max_search = STEPS_PER_REVOLUTION * 10  # Allow searching up to 10 revolutions
        
        while home_steps < max_search:
            pulse_motor(FINE_speed_US)
            home_steps += 1
            
            if get_sensor_state() == 1:  # Home triggered!
                print(f"\n✓ home TRIGGERED!")
                print(f"  Distance to home: {home_steps} steps")
                disable_motor()
                led_pin.on()
                utime.sleep_ms(500)
                led_pin.off()
                
                print()
                print("=" * 60)
                print("✓ rotate & GO home COMPLETE!")
                print("=" * 60)
                print(f"Rotated: {degrees}°")
                print(f"Returned to home: {home_steps} steps")
                print()
                return
            
            if home_steps % 50 == 0:
                print(f"  Searching... {home_steps} steps", end="\r")
        
        print(f"\n✗ home NOT FOUND after {max_search} steps!")
        disable_motor()
        
    except ValueError:
        print("✗ Invalid input - enter a number")
    except Exception as e:
        print(f"✗ Error: {e}")
        disable_motor()

def full_home_cycle():
    """
    Complete home-finding cycle:
    1. Rotate to find home
    2. Stop
    3. Reverse and slowly approach home
    """
    print()
    print("=" * 60)
    print("FULL home-FINDING CYCLE")
    print("=" * 60)
    print()
    
    print("Select direction to search for home:")
    print("1. Clockwise (CW)")
    print("2. Counter-Clockwise (CCW)")
    print()
    print("Enter choice (1-2): ", end="")
    
    try:
        choice = input().strip()
        
        if choice == "1":
            direction = CW
        elif choice == "2":
            direction = CCW
        else:
            print("✗ Invalid choice")
            return
        
        print()
        
        # Phase 1: Find home
        home_steps = rotate_to_home(direction)
        
        if home_steps == -1:
            print("\n✗ CYCLE FAILED: Could not find home")
            return
        
        # Pause between phases
        print()
        print("Pausing 2 seconds before reverse...")
        utime.sleep(2)
        
        # Phase 2: Reverse and fine-tune
        return_steps = reverse_and_fine_tune(direction, home_steps)
        
        if return_steps == -1:
            print("\n✗ CYCLE FAILED: Could not re-trigger home")
            return
        
        # Complete!
        print()
        print("=" * 60)
        print("✓ FULL CYCLE COMPLETE!")
        print("=" * 60)
        print(f"Phase 1 (Find home): {home_steps} steps")
        print(f"Phase 2 (Return to home): {return_steps} steps")
        print(f"Total distance: {home_steps + return_steps} steps")
        print()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        disable_motor()

# ============================================================
# MAIN MENU
# ============================================================

def main_menu():
    """Interactive test menu"""
    while True:
        print("\n" + "=" * 60)
        print("stepper MOTOR home FINDING - Main Menu")
        print("=" * 60)
        print()
        print("1. Run full home-finding cycle")
        print("2. Just find home (Phase 1 only)")
        print("3. Rotate & go home (custom rotation then return)")
        print("4. Show configuration")
        print("5. Exit")
        print()
        print("Enter choice (1-5): ", end="")
        
        try:
            choice = input().strip()
            
            if choice == "1":
                full_home_cycle()
            
            elif choice == "2":
                print()
                print("Select direction to search:")
                print("1. CW (Clockwise)")
                print("2. CCW (Counter-Clockwise)")
                print("Enter choice (1-2): ", end="")
                dir_choice = input().strip()
                
                if dir_choice == "1":
                    rotate_to_home(CW)
                elif dir_choice == "2":
                    rotate_to_home(CCW)
                else:
                    print("✗ Invalid choice")
            
            elif choice == "3":
                rotate_then_go_home()
            
            elif choice == "4":
                print()
                print("=" * 60)
                print("CONFIGURATION")
                print("=" * 60)
                print(f"Initial speed: {INITIAL_speed_US}µs per pulse")
                print(f"Fine-tuning speed: {FINE_speed_US}µs per pulse")
                print(f"Steps per revolution: {STEPS_PER_REVOLUTION}")
                print(f"Degrees per step: {DEGREES_PER_STEP}°")
                print(f"Sensor pin: GPIO {SENSOR_PIN} (active LOW)")
                print("=" * 60)
            
            elif choice == "5":
                print("\nExiting...")
                disable_motor()
                led_pin.off()
                print("✓ Safe shutdown complete")
                break
            
            else:
                print("✗ Invalid choice - please select 1-5")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            disable_motor()
            led_pin.off()
            break
        
        except Exception as e:
            print(f"✗ Error: {e}")
            disable_motor()

# ============================================================
# STARTUP
# ============================================================

print("Speed Configuration:")
print(f"  Initial approach: {INITIAL_speed_US}µs (faster)")
print(f"  Fine-tuning: {FINE_speed_US}µs (very slow, precise)")
print()
print("Motor will:")
print("  1. Rotate at initial speed until home sensor triggers")
print("  2. Stop and reverse direction")
print("  3. Very slowly approach home again until sensor re-triggers")
print()

# Start main menu
main_menu()
