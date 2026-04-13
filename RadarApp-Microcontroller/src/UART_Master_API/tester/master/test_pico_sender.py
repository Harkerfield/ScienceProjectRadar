# MicroPython - Pico Test Sender
# Continuously sends test data to Raspberry Pi via UART0
# Upload this to Pico to test Pi listener

from machine import UART, Pin
import utime
from utime import sleep

# LED indicator
led = Pin("LED", Pin.OUT)

# UART0: Communication with Raspberry Pi
uart_server = UART(0, baudrate=460800, tx=Pin(16), rx=Pin(17))

print("[STARTUP] Pico Test Sender initialized")
print("[STARTUP] Sending test data to Raspberry Pi every 2 seconds")
print("=" * 60)

counter = 0

while True:
    try:
        # Flash LED to show activity
        led.on()
        
        counter += 1
        
        # Create test message
        test_messages = [
            f"TEST:ping:{counter}",
            f"servo:status:OK",
            f"stepper:speed:100",
            f"radar:DISTANCE:45",
        ]
        
        msg = test_messages[counter % len(test_messages)]
        
        # Send message
        uart_server.write(f"{msg}\n".encode())
        print(f"[SENT] → {msg}")
        
        led.off()
        
        # Wait 2 seconds
        sleep(2)
        
    except Exception as e:
        print(f"[error] {e}")
        led.on()
        sleep(1)
