from machine import Pin, PWM
import time

# --- Configuration ---
# Set up direction and step pins
# Setup Pins
pulse_pin = PWM(Pin(5))
dir_pin = Pin(6, Pin.OUT)
en_pin = Pin(7, Pin.OUT)


# Sets the frequency to 100Hz for initial speed
pulse_pin.freq(50) 
# 50% duty cycle (32768/65535) creates the necessary square wave pulses
pulse_pin.duty_u16(32768) 

def set_speed(frequency):
    """Sets speed based on frequency (Hz)"""
    if frequency > 0:
        pulse_pin.freq(frequency)
    else:
        pulse_pin.duty_u16(0) # Stop if frequency is 0

# --- Main Movement Loop ---
try:
    while True:
        # Move Forward
        dir_pin.on()
        set_speed(100) # Slow speed = more holding torque
        time.sleep(10)
        
        # Move Backward
        dir_pin.off()
        set_speed(100) # Same slow speed for consistency
        time.sleep(10)
        
except KeyboardInterrupt:
    # Stop motor on exit
    pulse_pin.duty_u16(0)                
