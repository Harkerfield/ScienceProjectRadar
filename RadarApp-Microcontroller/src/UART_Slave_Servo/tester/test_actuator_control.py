from machine import Pin, PWM
import time

# ============================================================
# servo CONTROL - Test Code
# ============================================================
# Controls a linear servo via PWM on GPIO 2
# Frequency: 50Hz (standard for servo control)
# Duty cycle: 6553 (open), 3277 (closed)
# ============================================================

# Static configuration variables
GPIO_PIN = 2          # PWM output pin for servo control
FREQUENCY = 50        # PWM frequency in Hz
open_DUTY = 6553      # Duty cycle for fully open position
close_DUTY = 3277     # Duty cycle for fully closed position

# Initialize PWM on the specified GPIO pin
motor_pwm = PWM(Pin(GPIO_PIN))
motor_pwm.freq(FREQUENCY)

def open_fully():
    """
    Open servo to maximum position
    Sets PWM duty to open_DUTY value
    """
    motor_pwm.duty_u16(open_DUTY)

def close_fully():
    """
    Close servo to minimum position
    Sets PWM duty to close_DUTY value
    """
    motor_pwm.duty_u16(close_DUTY)

def main_menu():
    """
    Interactive menu loop for servo control
    Allows user to open, close, or exit the program
    """
    while True:
        # Display menu header
        print("\n" + "=" * 40)
        print("servo CONTROL")
        print("=" * 40)
        print(f"GPIO: {GPIO_PIN} | Freq: {FREQUENCY}Hz")
        print()
        print("1. Open")
        print("2. Close")
        print("3. Exit")
        print()
        print("Enter choice (1-3): ", end="")
        
        try:
            choice = input().strip()
            
            if choice == "1":
                print("Opening...")
                open_fully()
            elif choice == "2":
                print("Closing...")
                close_fully()
            elif choice == "3":
                print("Exiting...")
                motor_pwm.deinit()
                break
            else:
                print("✗ Invalid choice")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted")
            motor_pwm.deinit()
            break
        except Exception as e:
            print(f"Error: {e}")

# Start the main menu loop
main_menu()
