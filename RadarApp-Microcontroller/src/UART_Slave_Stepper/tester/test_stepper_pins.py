# Stepper Motor Basic Pin Setup Tester
# Step 1: Initialize and test stepper motor and sensor pins
from machine import Pin
import time

print("=" * 60)
print("stepper MOTOR PIN SETUP TEST - Step 1")
print("=" * 60)
print()

# ============================================================
# PIN CONFIGURATION
# ============================================================

# Stepper motor control pins (DRV8825 driver)
pul_pin = Pin(5, Pin.OUT)      # Pulse pin - triggers one step
dir_pin = Pin(6, Pin.OUT)      # Direction pin - CW(HIGH) or CCW(LOW)
ena_pin = Pin(7, Pin.OUT)      # Enable pin - LOW=enabled, HIGH=disabled

# Home sensor pin (inductive PNP sensor)
sensor_pin = Pin(20, Pin.IN, Pin.PULL_UP)  # Active LOW when metal detected

# Status LED
led_pin = Pin("LED", Pin.OUT)

# ============================================================
# INITIAL STATE
# ============================================================

# Set initial pin states
ena_pin.on()  # Disable motor initially (HIGH = disabled)
pul_pin.off() # Pulse off
dir_pin.on()  # Direction CW

print("✓ Pin initialization complete")
print()

# ============================================================
# PIN status DISPLAY
# ============================================================

def display_pin_status():
    """Display current status of all pins"""
    print()
    print("PIN status:")
    print("-" * 60)
    print(f"  GPIO 5 (PUL):    {pul_pin.value()} (0=LOW, 1=HIGH)")
    print(f"  GPIO 6 (DIR):    {dir_pin.value()} (0=CCW, 1=CW)")
    print(f"  GPIO 7 (ENA):    {ena_pin.value()} (0=enableD, 1=disableD)")
    print(f"  GPIO 20 (SENSOR): {sensor_pin.value()} (0=METAL_DETECTED, 1=CLEAR)")
    print(f"  LED:             {led_pin.value()} (0=OFF, 1=ON)")
    print("-" * 60)
    print()

# ============================================================
# PIN TEST FUNCTIONS
# ============================================================

def test_pulse_pin():
    """Test pulse pin - toggle it 10 times"""
    print("\n[TEST] Pulse Pin (GPIO 5)")
    print("Toggling pulse pin 10 times...")
    
    for i in range(10):
        pul_pin.on()
        time.sleep_ms(100)
        pul_pin.off()
        time.sleep_ms(100)
        print(f"  Toggle {i+1}/10", end="\r")
    
    print()
    print("✓ Pulse pin test complete")
    print(f"  Final state: {pul_pin.value()}")

def test_direction_pin():
    """Test direction pin - toggle between CW and CCW"""
    print("\n[TEST] Direction Pin (GPIO 6)")
    
    print("Setting to CW (HIGH)...")
    dir_pin.on()
    time.sleep(1)
    print(f"  DIR state: {dir_pin.value()}")
    
    print("Setting to CCW (LOW)...")
    dir_pin.off()
    time.sleep(1)
    print(f"  DIR state: {dir_pin.value()}")
    
    print("✓ Direction pin test complete")

def test_enable_pin():
    """Test enable pin - toggle motor enable/disable"""
    print("\n[TEST] Enable Pin (GPIO 7)")
    
    print("Enabling motor (LOW)...")
    ena_pin.off()
    time.sleep(1)
    print(f"  ENA state: {ena_pin.value()} (motor should be enableD)")
    
    print("Disabling motor (HIGH)...")
    ena_pin.on()
    time.sleep(1)
    print(f"  ENA state: {ena_pin.value()} (motor should be disableD)")
    
    print("✓ Enable pin test complete")

def test_sensor_pin():
    """Test sensor pin - read current state"""
    print("\n[TEST] Sensor Pin (GPIO 20)")
    print("Reading sensor pin state 5 times...")
    
    for i in range(5):
        state = sensor_pin.value()
        state_label = "METAL DETECTED" if state == 0 else "CLEAR"
        print(f"  Reading {i+1}/5: {state} ({state_label})")
        time.sleep(500)
    
    print("✓ Sensor pin test complete")
    print("Note: Move metal near sensor to see state changes")

def test_led():
    """Test LED - toggle it 5 times"""
    print("\n[TEST] Status LED")
    print("Blinking LED 5 times...")
    
    for i in range(5):
        led_pin.on()
        time.sleep_ms(200)
        led_pin.off()
        time.sleep_ms(200)
        print(f"  Blink {i+1}/5", end="\r")
    
    print()
    print("✓ LED test complete")
    led_pin.off()  # Ensure LED is off

# ============================================================
# MAIN MENU
# ============================================================

def main_menu():
    """Interactive test menu"""
    while True:
        print("\n" + "=" * 60)
        print("stepper MOTOR PIN SETUP - Main Menu")
        print("=" * 60)
        print()
        print("1. Display pin status")
        print("2. Test pulse pin (GPIO 5)")
        print("3. Test direction pin (GPIO 6)")
        print("4. Test enable pin (GPIO 7)")
        print("5. Test sensor pin (GPIO 20)")
        print("6. Test LED")
        print("7. Run all tests")
        print("8. Exit")
        print()
        print("Enter choice (1-8): ", end="")
        
        try:
            choice = input().strip()
            
            if choice == "1":
                display_pin_status()
            
            elif choice == "2":
                test_pulse_pin()
            
            elif choice == "3":
                test_direction_pin()
            
            elif choice == "4":
                test_enable_pin()
            
            elif choice == "5":
                test_sensor_pin()
            
            elif choice == "6":
                test_led()
            
            elif choice == "7":
                print("\n" + "=" * 60)
                print("RUNNING ALL TESTS")
                print("=" * 60)
                display_pin_status()
                test_pulse_pin()
                test_direction_pin()
                test_enable_pin()
                test_led()
                test_sensor_pin()
                print("\n" + "=" * 60)
                print("✓ ALL TESTS COMPLETE")
                print("=" * 60)
            
            elif choice == "8":
                print("\nExiting...")
                # Ensure safe state before exit
                ena_pin.on()  # Disable motor
                led_pin.off()
                print("✓ Motor disabled, LED off")
                break
            
            else:
                print("✗ Invalid choice - please select 1-8")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            # Ensure safe state
            ena_pin.on()  # Disable motor
            led_pin.off()
            print("✓ Motor disabled, LED off")
            break
        
        except Exception as e:
            print(f"✗ Error: {e}")

# ============================================================
# STARTUP
# ============================================================

print("Pin Configuration Summary:")
print("  Motor Pins:")
print("    - GPIO 5:  Pulse (PUL)")
print("    - GPIO 6:  Direction (DIR)")
print("    - GPIO 7:  Enable (ENA)")
print("  Sensor:")
print("    - GPIO 20: Inductive home sensor")
print("  Status:")
print("    - LED:     Built-in status indicator")
print()

print("Initial Safe State:")
print(f"  Motor enabled: {ena_pin.value() == 0} (ENA={'disableD' if ena_pin.value() == 1 else 'enableD'})")
print(f"  Direction: {'CW' if dir_pin.value() == 1 else 'CCW'} (DIR={dir_pin.value()})")
print(f"  Pulse: {pul_pin.value()}")
print()

# Start main menu
main_menu()
