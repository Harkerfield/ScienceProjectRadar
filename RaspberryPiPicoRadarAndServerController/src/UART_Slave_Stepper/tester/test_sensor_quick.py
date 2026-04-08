# Quick Inductive Sensor Test
# Wire colors: Brown, Blue, Black
# Wiring:
#   Brown = 6-36V DC power (external power supply)
#   Blue  = Ground (0V, connect to Pico GND and power supply GND)
#   Black = Signal output (PNP) -> GPIO 20 (LOW when metal detected)
from machine import Pin
import utime

sensor = Pin(20, Pin.IN, Pin.PULL_UP)  # PNP sensor: normally HIGH, goes LOW on detection
led = Pin("LED", Pin.OUT)

print("Inductive Sensor Test")
print("=" * 40)
print("Wire colors:")
print("  Brown -> 6-36V power")
print("  Blue  -> Ground (GND)")
print("  Black -> GPIO 20 (PNP signal)")
print("=" * 40)
print("Bring metal near sensor...")
print()

try:
    while True:
        state = sensor.value()
        status = "🔴 METAL!" if state == 1 else "⚪ Clear "  # Inverted: HIGH = metal detected
        print(f"{status} (GPIO 20: {state})", end="\r")
        led.value(state)  # LED on when metal detected
        utime.sleep_ms(100)

except KeyboardInterrupt:
    print("\nTest stopped")
    led.off()
