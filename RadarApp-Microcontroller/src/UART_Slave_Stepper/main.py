# MicroPython UART Slave - Stepper Motor Controller
# NOTE: This code runs on Raspberry Pi Pico only, not on standard Python
# Requires MicroPython firmware installed on Pico
# UART Slave (on shared UART1 bus with device addressing)
# Command Format: stepper:COMMAND[:ARGS]
# Response Format: stepper:status[:DATA]
# Commands: ping, status, whoami, spin:<speed>, stop, home, move:<angle>, rotate:<degrees>, enable, disable, speed:<us>

from machine import UART, Pin
import utime
import sys
import select

# Display MicroPython version
print("=" * 50)
print(f"MicroPython Version: {sys.version}")
print(f"MicroPython Implementation: {sys.implementation}")
print("=" * 50)

# ============================================================
# UART CONFIGURATION
# ============================================================
# UART1: Slave communication bus (shared with servo and radar)
uart_slaves = UART(1, baudrate=115200, tx=Pin(4), rx=Pin(5))
print("[STARTUP] UART slave initialized (TX=GPIO4, RX=GPIO5)")

# ============================================================
# PIN SETUP
# ============================================================

# Disable WiFi/Bluetooth to avoid CYW43 interference
try:
    import network
    network.country('US')  # Set country first
    wlan = network.WLAN(network.STA_IF)
    wlan.active(False)
    print("[OK] WiFi disabled")
except Exception as e:
    print(f"[WARN] WiFi disable failed: {e}")

# LED for activity indication
led = Pin("LED", Pin.OUT)
led.on()
print("[INIT] LED turned ON")


# Stepper Motor Driver Pins
PUL_PIN = 5              # Pulse pin
DIR_PIN = 6              # Direction pin
ENA_PIN = 7              # Enable pin

# Sensor Pin
SENSOR_PIN = 20          # Inductive home sensor

pul_pin = Pin(PUL_PIN, Pin.OUT)
dir_pin = Pin(DIR_PIN, Pin.OUT)
ena_pin = Pin(ENA_PIN, Pin.OUT)
home_sensor = Pin(SENSOR_PIN, Pin.IN, Pin.PULL_UP)

pul_pin.off()
dir_pin.on()  # CW
ena_pin.on()  # Disabled

# ============================================================
# STATIC CONFIGURATION VARIABLES
# ============================================================

# Motor configuration
STEPS_PER_REVOLUTION = 600       # With gear reduction (200 * 3:1 = 600)
DEGREES_PER_STEP = 0.6           # 360 / 600

# Speed configuration (in microseconds for pulse duration)
INITIAL_speed_US = 2000          # Initial rotation speed (2000µs per pulse) - SLOW for torque
FINE_speed_US = 3000             # Fine-tuning speed (3000µs per pulse) - even slower
MIN_speed_US = 500               # Minimum speed (fastest: 500µs per pulse)
MAX_speed_US = 10000             # Maximum speed (slowest: 10000µs per pulse)

# Direction definitions
CW = 1
CCW = 0

# State tracking
stepper_position = 0             # Current position in degrees (calculated from home)
stepper_enabled = False          # Motor enabled state
stepper_at_home = False          # At home flag
current_speed_us = INITIAL_speed_US  # Current speed setting
home_calibrated = False          # Whether home has been found and calibrated

# Continuous rotation state
continuous_rotating = False      # Whether in continuous rotation mode
continuous_direction = CW        # Direction for continuous rotation (1=CW, 0=CCW)
continuous_revolutions = 0       # Count of complete 360° rotations
home_last_state = 0              # Track last sensor state to detect changes

# ============ SETTINGS SYSTEM ============
# Store all configurable settings
stepper_settings = {
    'direction': 0,              # 0=CCW, 1=CW
    'speed': INITIAL_speed_US,   # pulse microseconds
    'acceleration': 0,           # 0=no acceleration
    'home_position': 0,          # Home angle in degrees
    'max_speed': 100,            # minimum pulse time in us
    'min_speed': 2000,           # maximum pulse time in us
    'enabled': 0,                # 1=enabled, 0=disabled
    'position': 0,               # Current position in degrees
    'at_home': 0,                # 1=at home, 0=not at home
    'sensor_state': 0,           # 0=triggered, 1=clear
}

# ============ DEVICE IDENTIFICATION ============
device_name = "stepper"

# Track startup time for uptime reporting
startup_time = utime.ticks_ms()

# ============ UART COMMUNICATION LAYER ============

def flush_uart_buffer():
    """Clear any stale data in UART buffer"""
    while uart_slaves.any():
        uart_slaves.read()
    utime.sleep_ms(50)

def send_uart_response(status_msg):
    """
    Send device-addressed response via UART.
    Format: stepper:OK:key=val:key=val\n
    
    Args:
        status_msg: Status message (e.g., "OK:POS=45" or "error:not_calibrated")
    """
    response = f"{device_name}:{status_msg}\n"
    uart_slaves.write(response.encode())
    print(f"[UART-SEND] {response.strip()}")
    return response

def simple_response(cmd, status, **kwargs):
    """Create simple text response - colon-separated format
    Format: COMMAND:status:key=val:key=val
    Example: status:OK:ANGLE=45:enableD=1
    """
    parts = [status]
    for k, v in kwargs.items():
        parts.append(f"{k}={v}")
    return ":".join(parts)

# I2C Command Protocol (LEGACY - replaced by UART)
# FORMAT: [COMMAND_BYTE][SETTING_ID][VALUE_BYTES...]
# COMMAND_BYTE:
#   0x01 = SET setting (followed by setting_id and value)
#   0x02 = GET setting (followed by setting_id)
#   0x03 = GET status (returns all settings)
#   0x04 = ACTION (move, home, etc.)
#
# ACTION IDs (for command 0x04):
#   0x01 = FIND home
#   0x02 = move to angle

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def pulse_motor(speed_us):
    """Send a single pulse to stepper motor"""
    pul_pin.on()
    utime.sleep_us(speed_us)
    pul_pin.off()
    utime.sleep_us(speed_us)

def enable_motor():
    """Enable stepper motor"""
    global stepper_enabled
    ena_pin.off()  # LOW enables motor
    stepper_enabled = True
    stepper_settings['enabled'] = 1
    print("[stepper] Motor enabled")

def disable_motor():
    """Disable stepper motor"""
    global stepper_enabled
    ena_pin.on()  # HIGH disables motor
    pul_pin.off()
    stepper_enabled = False
    stepper_settings['enabled'] = 0
    print("[stepper] Motor disabled")

def set_direction(direction):
    """Set motor direction: CW (1) or CCW (0)"""
    dir_pin.value(direction)
    stepper_settings['direction'] = direction
    dir_label = "CW" if direction == CW else "CCW"
    print(f"[stepper] Direction: {dir_label}")

def get_sensor_state():
    """Read sensor state: 1=triggered, 0=clear"""
    return home_sensor.value()

def rotate_stepper_relative(delta_angle):
    """Rotate stepper by a relative amount from current position"""
    global stepper_position, stepper_at_home, current_speed_us
    
    if not home_calibrated:
        print("[stepper] error: Must find home first before rotating!")
        return False
    
    # Calculate target angle
    target_angle = (stepper_position + delta_angle) % 360
    
    # Convert angle to steps
    steps_needed = int(abs(delta_angle) / DEGREES_PER_STEP)
    
    if steps_needed == 0:
        print(f"[stepper] Rotation too small ({delta_angle}°)")
        return True
    
    # Set direction
    is_clockwise = delta_angle > 0
    set_direction(CW if is_clockwise else CCW)
    
    # Enable motor
    enable_motor()
    
    # Generate pulses and count steps
    print(f"[stepper] Rotating {delta_angle:.1f}° ({steps_needed} steps)")
    for _ in range(steps_needed):
        pulse_motor(current_speed_us)
        # Update position in real-time
        stepper_position += (delta_angle / abs(delta_angle)) * DEGREES_PER_STEP
    
    # Normalize final position to 0-360
    stepper_position = stepper_position % 360
    
    # Check if at home
    stepper_at_home = (abs(stepper_position) < DEGREES_PER_STEP * 0.5)
    stepper_settings['position'] = int(stepper_position)
    stepper_settings['at_home'] = 1 if stepper_at_home else 0
    
    print(f"[stepper] Rotated to {stepper_position:.1f}°")
    return True

def move_stepper_direct(angle):
    """Move stepper to target angle - tracks position by counting pulses from home"""
    global stepper_position, stepper_at_home, current_speed_us
    
    if not home_calibrated:
        print("[stepper] error: Must find home first before moving!")
        return False
    
    # Normalize angles
    target_angle = angle % 360
    current_angle = stepper_position % 360
    
    # Calculate shortest path
    delta = target_angle - current_angle
    if delta > 180:
        delta -= 360
    elif delta < -180:
        delta += 360
    
    # Convert angle to steps
    steps_needed = int(abs(delta) / DEGREES_PER_STEP)
    
    if steps_needed == 0:
        print(f"[stepper] Already at {stepper_position}°")
        stepper_at_home = (stepper_position == 0)
        return True
    
    # Set direction
    is_clockwise = delta > 0
    set_direction(CW if is_clockwise else CCW)
    
    # Enable motor
    enable_motor()
    
    # Generate pulses and count steps to calculate position
    print(f"[stepper] Moving {steps_needed} steps ({delta:.1f}°)")
    for _ in range(steps_needed):
        pulse_motor(current_speed_us)
        # Update position in real-time
        stepper_position += (delta / abs(delta)) * DEGREES_PER_STEP  # +/- DEGREES_PER_STEP
    
    # Normalize final position to 0-360
    stepper_position = stepper_position % 360
    
    # Check if at home (position == 0)
    stepper_at_home = (abs(stepper_position) < DEGREES_PER_STEP * 0.5)
    stepper_settings['position'] = int(stepper_position)
    stepper_settings['at_home'] = 1 if stepper_at_home else 0
    
    print(f"[stepper] Arrived at {stepper_position:.1f}°")
    return True

def find_home_complete():
    """Complete home-finding cycle (2-phase) - calibrates position to 0°"""
    global stepper_position, stepper_at_home, home_calibrated
    
    print("[home] Starting complete home-finding sequence...")
    print()
    
    # PHASE 1: Fast search
    print("[PHASE 1] Fast search for home")
    set_direction(CCW)
    enable_motor()
    
    initial_sensor = get_sensor_state()
    print(f"Initial sensor: {initial_sensor} (1=home, 0=CLEAR)")
    
    # If already at home, move away first
    if initial_sensor == 1:
        print("Sensor already triggered, moving away...")
        set_direction(CW)
        away_steps = 0
        max_away = STEPS_PER_REVOLUTION * 2
        
        while away_steps < max_away:
            pulse_motor(INITIAL_speed_US)
            away_steps += 1
            
            if get_sensor_state() == 0:  # Cleared
                print(f"Cleared after {away_steps} steps")
                break
            
            if away_steps % 100 == 0:
                print(f"Moving away... {away_steps} steps")
        
        set_direction(CCW)  # Back to search direction
        utime.sleep_ms(100)
    
    # Rotate until sensor triggers
    phase1_steps = 0
    max_steps = STEPS_PER_REVOLUTION * 5
    
    print(f"Searching up to {max_steps} steps...")
    
    while phase1_steps < max_steps:
        pulse_motor(INITIAL_speed_US)
        phase1_steps += 1
        
        if get_sensor_state() == 1:  # Home found!
            print(f"home TRIGGERED at {phase1_steps} steps!")
            angle = phase1_steps * DEGREES_PER_STEP
            print(f"  Angle: {angle:.1f}°")
            break
        
        if phase1_steps % 100 == 0:
            angle = (phase1_steps % STEPS_PER_REVOLUTION) * DEGREES_PER_STEP
            revs = phase1_steps / STEPS_PER_REVOLUTION
            print(f"  Progress: {revs:.1f}R + {angle:.1f}°")
    
    if phase1_steps == max_steps:
        print("home NOT FOUND after max steps!")
        disable_motor()
        return False
    
    # PHASE 2: Fine-tune approach
    print()
    print("[PHASE 2] Fine-tune approach")
    utime.sleep_ms(500)
    
    set_direction(CW)  # Reverse direction
    
    phase2_steps = 0
    max_fine = phase1_steps + 100
    
    print(f"Slowly approaching home...")
    
    while phase2_steps < max_fine:
        pulse_motor(FINE_speed_US)
        phase2_steps += 1
        
        if get_sensor_state() == 1:  # Home re-triggered!
            print(f"home RE-TRIGGERED at {phase2_steps} steps!")
            led.on()
            utime.sleep_ms(500)
            led.off()
            
            # Set position to home (0°) and calibrate
            stepper_position = 0
            stepper_at_home = True
            home_calibrated = True  # Home is now calibrated - ignore sensor after this
            stepper_settings['position'] = 0
            stepper_settings['at_home'] = 1
            enable_motor()
            
            print()
            print("=" * 60)
            print("home FINDING COMPLETE!")
            print(f"Phase 1: {phase1_steps} steps")
            print(f"Phase 2: {phase2_steps} steps")
            print("Position set to 0° (home)")
            print("Position tracking enabled")
            print("=" * 60)
            return True
        
        if phase2_steps % 50 == 0:
            print(f"  Approaching... {phase2_steps} steps")
    
    print("PHASE 2 FAILED: Did not re-trigger home")
    disable_motor()
    return False

def find_home_fast():
    """Quick home finding (phase 1 only) - calibrates position to 0°"""
    global stepper_position, stepper_at_home, home_calibrated
    
    print("[home] Quick home search...")
    set_direction(CCW)
    enable_motor()
    
    steps = 0
    max_steps = STEPS_PER_REVOLUTION * 5
    
    while steps < max_steps:
        pulse_motor(INITIAL_speed_US)
        steps += 1
        
        if get_sensor_state() == 1:  # Found!
            print(f"home FOUND at {steps} steps")
            stepper_position = 0
            stepper_at_home = True
            home_calibrated = True  # Home is now calibrated
            stepper_settings['position'] = 0
            stepper_settings['at_home'] = 1
            enable_motor()
            print("Position tracking enabled from home (0°)")
            return True
        
        if steps % 100 == 0:
            print(f"  Searching... {steps} steps")
    
    print("home NOT FOUND")
    disable_motor()
    return False

def run_continuous_rotation():
    """Continuously rotate stepper until stopped"""
    global stepper_position, continuous_revolutions, home_last_state, continuous_rotating
    
    if not stepper_enabled:
        enable_motor()
    
    print(f"[rotate] Continuous rotation started, direction: {'CW' if continuous_direction==CW else 'CCW'}")
    
    try:
        while continuous_rotating:
            # Pulse the motor
            pul_pin.on()
            utime.sleep_us(current_speed_us)
            pul_pin.off()
            utime.sleep_us(current_speed_us)
            
            # Update position
            if continuous_direction == CW:
                stepper_position += DEGREES_PER_STEP
            else:
                stepper_position -= DEGREES_PER_STEP
            
            # Handle revolutions
            if stepper_position >= 360:
                stepper_position -= 360
                continuous_revolutions += 1
            elif stepper_position < 0:
                stepper_position += 360
                continuous_revolutions += 1
            
            # Sensor check
            current_sensor = get_sensor_state()
            # Home detected messages disabled during continuous rotation
            # if current_sensor == 1 and home_last_state == 0:
            #     print(f"[SENSOR] home DETECTED at {stepper_position:.1f}° (Rev {continuous_revolutions})")
            home_last_state = current_sensor
            
    finally:
        disable_motor()
        print("[rotate] Continuous rotation stopped")



def process_uart_command(cmd_text):
    """Process UART command received from master.
    Format: stepper:COMMAND[:ARGS]
    Response: stepper:status[:DATA]
    
    Supports commands: ping, status, whoami, spin:<speed>, stop, home, move:<angle>, 
                       rotate:<degrees>, enable, disable, speed:<us>
    """
    global stepper_position, stepper_enabled, stepper_at_home, continuous_rotating, continuous_direction, continuous_revolutions, home_last_state, current_speed_us
    
    try:
        if not cmd_text:
            send_uart_response("error:empty_command")
            return
        
        # Parse command format: stepper:COMMAND[:ARGS]
        parts = cmd_text.strip().split(":", 2)  # Split on first 2 colons only
        
        if len(parts) < 2:
            send_uart_response("error:invalid_format")
            return
        
        device = parts[0].lower()
        if device != device_name:
            send_uart_response(f"error:wrong_device:{device}")
            return
        
        cmd = parts[1].lower()
        args = parts[2] if len(parts) > 2 else ""
        
        print(f"[UART-CMD] Device: {device}, Command: {cmd}, Args: {args}")
        
        # ========== STANDARD COMMANDS ==========
        if cmd == "commands":
            commands = "ping,whoami,status,home,move,rotate,spin,stop,enable,disable,speed"
            send_uart_response(f"ok:commands={commands}")
        
        elif cmd == "ping":
            uptime_ms = utime.ticks_ms() - startup_time
            uptime_s = uptime_ms // 1000
            send_uart_response(f"ok:msg=alive:uptime={uptime_s}s")
        
        elif cmd == "whoami":
            send_uart_response(f"ok:device=stepper:type=motor_controller")
        
        elif cmd == "status":
            state = "home" if stepper_at_home else "rotating" if continuous_rotating else "idle"
            send_uart_response(f"ok:state={state}:position={int(stepper_position)}:calibrated={1 if home_calibrated else 0}")
        
        # ========== MOTOR CONTROL COMMANDS ==========
        elif cmd == "spin":
            # Start spinning (continuation rotation)
            if args:
                try:
                    speed = int(args)
                    if MIN_speed_US <= speed <= MAX_speed_US:
                        current_speed_us = speed
                        continuous_rotating = True
                        continuous_direction = CW
                        enable_motor()
                        send_uart_response(f"ok:msg=spin_started:speed={speed}:direction=cw")
                    else:
                        send_uart_response(f"error:speed_out_of_range:min={MIN_speed_US}:max={MAX_speed_US}")
                except ValueError:
                    send_uart_response("error:invalid_speed")
            else:
                send_uart_response("error:speed_required")
        
        elif cmd == "stop":
            if continuous_rotating:
                continuous_rotating = False
                disable_motor()
                send_uart_response(f"ok:msg=stopped:position={int(stepper_position)}:revolutions={continuous_revolutions}")
            else:
                send_uart_response("error:not_rotating")
        
        elif cmd == "speed":
            if args:
                try:
                    speed = int(args)
                    if MIN_speed_US <= speed <= MAX_speed_US:
                        current_speed_us = speed
                        stepper_settings['speed'] = speed
                        send_uart_response(f"ok:msg=speed_set:speed={speed}")
                    else:
                        send_uart_response(f"error:speed_out_of_range:min={MIN_speed_US}:max={MAX_speed_US}")
                except ValueError:
                    send_uart_response("error:invalid_speed")
            else:
                send_uart_response(f"ok:msg=current_speed:speed={current_speed_us}")
        
        elif cmd == "home":
            # Start home finding process
            continuous_rotating = False
            result = find_home_complete()
            if result:
                send_uart_response(f"ok:msg=home_found:position=0:calibrated=1")
            else:
                send_uart_response("error:home_not_found")
        
        elif cmd == "move":
            if args:
                try:
                    angle = float(args)
                    continuous_rotating = False
                    if not home_calibrated:
                        send_uart_response("error:not_calibrated")
                    else:
                        result = move_stepper_direct(angle)
                        if result:
                            send_uart_response(f"ok:msg=moved:position={int(stepper_position)}:target={int(angle)}")
                        else:
                            send_uart_response("error:move_failed")
                except ValueError:
                    send_uart_response("error:invalid_angle")
            else:
                send_uart_response("error:angle_required")
        
        elif cmd == "rotate":
            if args:
                try:
                    delta = float(args)
                    continuous_rotating = False
                    if not home_calibrated:
                        send_uart_response("error:not_calibrated")
                    else:
                        result = rotate_stepper_relative(delta)
                        if result:
                            send_uart_response(f"ok:msg=rotated:position={int(stepper_position)}:delta={int(delta)}")
                        else:
                            send_uart_response("error:rotate_failed")
                except ValueError:
                    send_uart_response("error:invalid_delta")
            else:
                send_uart_response("error:delta_required")
        
        elif cmd == "enable":
            enable_motor()
            send_uart_response("ok:msg=enabled:enabled=1")
        
        elif cmd == "disable":
            disable_motor()
            send_uart_response("ok:msg=disabled:enabled=0")
        
        else:
            send_uart_response(f"error:unknown_command:{cmd}")
    
    except Exception as e:
        print(f"[UART-ERR] Command processing error: {type(e).__name__}: {e}")
        send_uart_response(f"error:command_error:{str(e)[:30]}")

def process_i2c_command(cmd_bytes):
    """Process I2C command from master - Simple text protocol
    
    Supports text commands with simple responses:
    - ping → ping:OK
    - status → status:OK:POS=45:STATE=idle
    - POSITION → POSITION:OK:POS=90:home=0
    - whoami → whoami:OK:stepper
    """
    global stepper_position, current_speed_us, home_calibrated
    
    try:
        if len(cmd_bytes) == 0:
            result = b"error:EMPTY_CMD"
            print(f"[CMD] Empty command response: {result}")
            return result
        
        # Try to decode as text command
        try:
            cmd = cmd_bytes.decode().strip().lower()
        except Exception as de:
            print(f"[CMD] Decode error: {de}")
            result = b"error:DECODE_FAILED"
            print(f"[CMD] Decode error response: {result}")
            return result
        
        print(f"[CMD] Processing: {cmd}")
        
        # ping - Alive check
        if cmd == 'ping':
            result = simple_response("ping", "OK").encode()
            print(f"[CMD] ping response: {result}")
            return result
        
        # status - Get current status
        elif cmd == 'status':
            state = 'home' if stepper_at_home else 'ROTATING' if continuous_rotating else 'IDLE'
            result = simple_response("status", "OK",
                POS=int(stepper_position),
                STATE=state,
                enableD=1 if stepper_enabled else 0,
                CALIB=1 if home_calibrated else 0).encode()
            print(f"[CMD] status response: {result}")
            return result
        
        # POSITION - Get current position
        elif cmd == 'POSITION':
            result = simple_response("POSITION", "OK",
                POS=int(stepper_position),
                home=1 if stepper_at_home else 0).encode()
            print(f"[CMD] POSITION response: {result}")
            return result
        
        # speed - Get current speed
        elif cmd == 'speed':
            result = simple_response("speed", "OK", speed=current_speed_us).encode()
            print(f"[CMD] speed response: {result}")
            return result
        
        # speed:value - Set speed
        elif cmd.startswith('speed:'):
            try:
                speed = int(cmd.split(':')[1])
                if MIN_speed_US <= speed <= MAX_speed_US:
                    current_speed_us = speed
                    result = simple_response("speed", "OK", SET=speed).encode()
                    print(f"[CMD] speed set response: {result}")
                    return result
                else:
                    result = b"error:speed_OUT_OF_RANGE"
                    print(f"[CMD] Speed out of range response: {result}")
                    return result
            except Exception as se:
                print(f"[CMD] Speed parse error: {se}")
                result = b"error:INVALID_speed"
                print(f"[CMD] Invalid speed response: {result}")
                return result
        
        # FIND_home - Calibrate home position
        elif cmd == 'FIND_home':
            result = simple_response("FIND_home", "OK", status="STARTED").encode()
            print(f"[CMD] FIND_home response: {result}")
            return result
        
        # enable - Enable motor
        elif cmd == 'enable':
            enable_motor()
            result = simple_response("enable", "OK", enableD=1).encode()
            print(f"[CMD] enable response: {result}")
            return result
        
        # disable - Disable motor
        elif cmd == 'disable':
            disable_motor()
            result = simple_response("disable", "OK", enableD=0).encode()
            print(f"[CMD] disable response: {result}")
            return result
        
        # whoami - Device identification
        elif cmd == 'whoami':
            result = simple_response("whoami", "OK", DEVICE="stepper", ADDR="0x10").encode()
            print(f"[CMD] whoami response: {result}")
            return result
        
        else:
            result = simple_response("error", "UNKNOWN_CMD", CMD=cmd).encode()
            print(f"[CMD] Unknown command response: {result}")
            return result
    
    except Exception as e:
        print(f"[CMD] Exception: {type(e).__name__}: {e}")
        result = b"error:COMMAND_EXCEPTION"
        print(f"[CMD] Exception response: {result}")
        return result

def simple_response(cmd, status, **kwargs):
    """Create simple text response - no JSON parsing needed
    Format: COMMAND:OK:key1=val1:key2=val2
    Example: status:OK:ANGLE=45:enableD=1
    """
    parts = [cmd, status]
    for k, v in kwargs.items():
        parts.append(f"{k}={v}")
    return ":".join(parts)

def process_usb_command(line):
    """Process USB serial command - same functionality as I2C
    Returns simple text format compatible with I2C protocol
    """
    global stepper_position, stepper_enabled, stepper_at_home, continuous_rotating, continuous_direction, continuous_revolutions, home_last_state, current_speed_us
    try:
        cmd = line.strip().lower()
        
        # HELP - list available commands or show detailed help for a command
        if cmd == 'HELP':
            print("=" * 60)
            print("stepper MOTOR CONTROLLER - Command Reference")
            print("=" * 60)
            print("Type HELP <command> for detailed help on a command")
            print()
            print("Available Commands:")
            print("  FIND_home, move, rotate, START_rotate, stop_rotate, SET_DIRECTION")
            print("  POSITION, status, AT_home, SENSOR")
            print("  speed, ping, enable, disable, HELP")
            print("=" * 60)
            return "OK: Help displayed"
        
        # Detailed help for specific commands
        elif cmd.startswith('HELP '):
            help_cmd = cmd.split(' ', 1)[1].strip().lower()
            
            if help_cmd == 'FIND_home':
                print("=" * 60)
                print("FIND_home - Calibrate home position")
                print("=" * 60)
                print("Usage: FIND_home")
                print()
                print("Description:")
                print("  Finds and calibrates the home position (0°)")
                print("  Uses a 2-phase approach:")
                print("    Phase 1: Fast search for sensor trigger")
                print("    Phase 2: Fine-tune approach to exact position")
                print()
                print("Requirements:")
                print("  - Motor must be enabled")
                print("  - Sensor must be configured and working")
                print()
                print("Notes:")
                print("  - Position is set to 0° after calibration")
                print("  - Required before using move or rotate")
                print("=" * 60)
                return "OK: FIND_home help displayed"
            
            elif help_cmd == 'move':
                print("=" * 60)
                print("move - Move to absolute angle")
                print("=" * 60)
                print("Usage: move:<angle>")
                print("Example: move:90")
                print()
                print("Description:")
                print("  Moves stepper to absolute angle (0-360°)")
                print("  Always takes shortest path to target")
                print()
                print("Requirements:")
                print("  - FIND_home must be called first")
                print("  - Motor must be enabled")
                print()
                print("Examples:")
                print("  move:0   - Move to 0° (home)")
                print("  move:90  - Move to 90°")
                print("  move:180 - Move to 180°")
                print("=" * 60)
                return "OK: move help displayed"
            
            elif help_cmd == 'rotate':
                print("=" * 60)
                print("rotate - Rotate by relative amount")
                print("=" * 60)
                print("Usage: rotate:<degrees>")
                print("Example: rotate:45")
                print()
                print("Description:")
                print("  Rotates stepper by relative amount from current position")
                print("  Positive values = clockwise, Negative values = counter-clockwise")
                print()
                print("Requirements:")
                print("  - FIND_home must be called first")
                print("  - Motor must be enabled")
                print()
                print("Examples:")
                print("  rotate:45   - Rotate 45° clockwise")
                print("  rotate:-30  - Rotate 30° counter-clockwise")
                print("  rotate:360  - Rotate one full revolution")
                print("=" * 60)
                return "OK: rotate help displayed"
            
            elif help_cmd == 'START_rotate':
                print("=" * 60)
                print("START_rotate - Start continuous rotation")
                print("=" * 60)
                print("Usage: START_rotate or START_rotate:<direction>")
                print("Example: START_rotate  or  START_rotate:CW")
                print()
                print("Description:")
                print("  Starts continuous rotation")
                print("  If direction is omitted, uses currently set direction")
                print("  If direction is specified, sets it before starting")
                print("  Rotation continues until stop_rotate is issued")
                print("  Position is tracked and updated continuously")
                print()
                print("Directions:")
                print("  CW  - Clockwise rotation")
                print("  CCW - Counter-clockwise rotation")
                print()
                print("Examples:")
                print("  START_rotate      - Rotate in current direction")
                print("  START_rotate:CW   - Rotate clockwise continuously")
                print("  START_rotate:CCW  - Rotate counter-clockwise continuously")
                print()
                print("Change direction with:")
                print("  SET_DIRECTION:CW  or  SET_DIRECTION:CCW")
                print()
                print("Stop with:")
                print("  stop_rotate")
                print("=" * 60)
                return "OK: START_rotate help displayed"
            
            elif help_cmd == 'stop_rotate':
                print("=" * 60)
                print("stop_rotate - Stop continuous rotation")
                print("=" * 60)
                print("Usage: stop_rotate")
                print()
                print("Description:")
                print("  Stops continuous rotation started by START_rotate")
                print("  Motor is disabled and position is locked")
                print()
                print("Examples:")
                print("  stop_rotate - Stop current rotation")
                print("=" * 60)
                return "OK: stop_rotate help displayed"
            
            elif help_cmd == 'SET_DIRECTION':
                print("=" * 60)
                print("SET_DIRECTION - Change rotation direction")
                print("=" * 60)
                print("Usage: SET_DIRECTION:<direction>")
                print("Example: SET_DIRECTION:CW")
                print()
                print("Description:")
                print("  Sets or changes the rotation direction")
                print("  Can be used before START_rotate or during rotation")
                print("  Always updates the motor pin immediately")
                print()
                print("Directions:")
                print("  CW  - Clockwise rotation")
                print("  CCW - Counter-clockwise rotation")
                print()
                print("Examples:")
                print("  SET_DIRECTION:CW  - Set to clockwise")
                print("  SET_DIRECTION:CCW - Set to counter-clockwise")
                print("=" * 60)
                return "OK: SET_DIRECTION help displayed"
            
            elif help_cmd == 'POSITION':
                print("=" * 60)
                print("POSITION - Get current position")
                print("=" * 60)
                print("Usage: POSITION")
                print()
                print("Description:")
                print("  Returns current stepper position in degrees (0-360°)")
                print("  Shows calibration status")
                print()
                print("Example output:")
                print("  Position: 90.6° (CALIBRATED)")
                print("=" * 60)
                return "OK: POSITION help displayed"
            
            elif help_cmd == 'status':
                print("=" * 60)
                print("status - Get full system status")
                print("=" * 60)
                print("Usage: status")
                print()
                print("Description:")
                print("  Returns comprehensive system status including:")
                print("  - Current position (degrees)")
                print("  - Home status")
                print("  - Sensor state")
                print("  - Calibration status")
                print()
                print("Example output:")
                print("  Position: 45.0°, Home: NOT_home, Sensor: CLEAR, Status: CALIBRATED")
                print("=" * 60)
                return "OK: status help displayed"
            
            elif help_cmd == 'speed':
                print("=" * 60)
                print("speed - Adjust motor speed")
                print("=" * 60)
                print("Usage: speed:<microseconds>")
                print("Example: speed:2000")
                print()
                print("Description:")
                print("  Sets pulse duration in microseconds")
                print("  Higher values = slower speed = stronger torque")
                print("  Lower values = faster speed = weaker torque")
                print()
                print("Valid Range:")
                print(f"  {MIN_speed_US}µs (fastest) to {MAX_speed_US}µs (slowest)")
                print()
                print("Examples:")
                print("  speed:500  - Fast (weak holding)")
                print("  speed:1000 - Medium")
                print("  speed:2000 - Slow (good holding)")
                print("  speed:5000 - Very slow (strong holding)")
                print("="*60)
                return "OK: speed help displayed"
            
            elif help_cmd == 'ping':
                print("=" * 60)
                print("ping - Alive check")
                print("=" * 60)
                print("Usage: ping")
                print()
                print("Description:")
                print("  Verify slave is alive and responding")
                print("  Used by master to check slave status")
                print()
                print("Response format:")
                print("  {\"s\":\"ok\",\"msg\":\"alive\",\"addr\":\"0x##\"}")
                print()
                print("Example:")
                print("  {\"s\":\"ok\",\"msg\":\"alive\",\"addr\":\"0x10\"}")
                print("="*60)
                return "OK: ping help displayed"
            else:
                print("Unknown command for help. Available:")
                print("  HELP FIND_home - Calibrate home")
                print("  HELP move - Move to angle")
                print("  HELP rotate - Rotate by amount")
                print("  HELP START_rotate - Start continuous rotation")
                print("  HELP stop_rotate - Stop rotation")
                print("  HELP SET_DIRECTION - Change rotation direction")
                print("  HELP speed - Adjust speed")
                print("  HELP ping - Alive check")
                print("  HELP POSITION - Get position")
                print("  HELP status - Get status")
                return f"Unknown command: {help_cmd}"
        
        # status - get full status
        elif cmd == 'status':
            return simple_response("status", "OK",
                POS=round(stepper_position, 1),
                home=1 if stepper_at_home else 0,
                SENSOR=home_sensor.value(),
                CALIB=1 if home_calibrated else 0,
                enableD=1 if stepper_enabled else 0,
                speed=current_speed_us)
        
        # move:<angle> - move to specific angle (requires home calibration)
        elif cmd.startswith('move:'):
            try:
                angle = float(cmd.split(':')[1])
                # Stop continuous rotation if running
                continuous_rotating = False
                if not home_calibrated:
                    return simple_response("error", "NOT_CALIBRATED")
                print(f"[USB] ACTION: move to {angle}°")
                result = move_stepper_direct(angle)
                return simple_response("move", "OK", POS=round(stepper_position, 1)) if result else simple_response("move", "error", MSG="move_failed")
            except:
                return simple_response("error", "INVALID_move_FORMAT")
        
        # rotate:<degrees> - rotate by relative amount from current position
        elif cmd.startswith('rotate:'):
            try:
                delta_angle = float(cmd.split(':')[1])
                # Stop continuous rotation if running
                continuous_rotating = False
                if not home_calibrated:
                    return simple_response("error", "NOT_CALIBRATED")
                print(f"[USB] ACTION: rotate by {delta_angle}°")
                result = rotate_stepper_relative(delta_angle)
                return simple_response("rotate", "OK", POS=round(stepper_position, 1)) if result else simple_response("rotate", "error", MSG="rotate_failed")
            except:
                return simple_response("error", "INVALID_rotate_FORMAT")
        
        # START_rotate or START_rotate:<direction> - start continuous rotation
        elif cmd == 'START_rotate' or cmd.startswith('START_rotate:'):
            if not home_calibrated:
                return simple_response("error", "NOT_CALIBRATED")
            
            # Parse optional direction argument
            if cmd.startswith('START_rotate:'):
                direction_str = cmd.split(':')[1].strip().lower()
                if direction_str == 'CW':
                    continuous_direction = CW
                elif direction_str == 'CCW':
                    continuous_direction = CCW
                else:
                    return simple_response("error", "INVALID_DIRECTION")
            else:
                # Use already-set direction
                direction_str = "CW" if continuous_direction == CW else "CCW"
            
            # Set flag and let main loop handle rotation (non-blocking)
            continuous_rotating = True
            enable_motor()
            print(f"[rotate] Continuous rotation started, direction: {direction_str}")
            return simple_response("START_rotate", "OK", DIR=direction_str)
        
        # SET_DIRECTION:<direction> - change rotation direction (during or before rotation)
        elif cmd.startswith('SET_DIRECTION:'):
            direction_str = cmd.split(':')[1].strip().lower()
            if direction_str == 'CW':
                continuous_direction = CW
            elif direction_str == 'CCW':
                continuous_direction = CCW
            else:
                return simple_response("error", "INVALID_DIRECTION")
            set_direction(continuous_direction)
            print(f"[rotate] Direction set to: {direction_str}")
            return simple_response("SET_DIRECTION", "OK", DIR=direction_str)
        
        # stop_rotate - stop continuous rotation
        elif cmd == 'stop_rotate':
            if continuous_rotating:
                continuous_rotating = False
                disable_motor()
                print(f"[USB] ACTION: stop CONTINUOUS ROTATION")
                print(f"  Final position: {stepper_position:.1f}°")
                print(f"  Total revolutions: {continuous_revolutions}")
                total = continuous_revolutions * 360 + stepper_position
                return simple_response("stop_rotate", "OK", POS=round(stepper_position, 1), REV=continuous_revolutions, TOTAL=round(total, 1))
            else:
                return simple_response("error", "NOT_ROTATING")
        
        # POSITION - get current position
        elif cmd == 'POSITION':
            total = continuous_revolutions * 360 + stepper_position if continuous_rotating else stepper_position
            return simple_response("POSITION", "OK", POS=round(stepper_position, 1), REV=continuous_revolutions, TOTAL=round(total, 1), CALIB=1 if home_calibrated else 0)
        
        # FIND_home - find home position
        elif cmd == 'FIND_home':
            print(f"[USB] ACTION: FIND home")
            result = find_home_complete()
            return simple_response("FIND_home", "OK", POS=0, CALIB=1) if result else simple_response("FIND_home", "error", MSG="home_not_found")
        
        # AT_home - check if at home
        elif cmd == 'AT_home':
            return simple_response("AT_home", "OK", status=1 if stepper_at_home else 0)
        
        # SENSOR - get sensor state
        elif cmd == 'SENSOR':
            return simple_response("SENSOR", "OK", STATE=home_sensor.value())
        
        # enable - enable motor
        elif cmd == 'enable':
            print(f"[USB] ACTION: enable motor")
            enable_motor()
            return simple_response("enable", "OK")
        
        # disable - disable motor
        elif cmd == 'disable':
            print(f"[USB] ACTION: disable motor")
            disable_motor()
            return simple_response("disable", "OK")
        
        # speed:<microseconds> - set motor speed
        elif cmd.startswith('speed:'):
            try:
                speed_str = cmd.split(':')[1].strip()
                speed_us = int(speed_str)
                
                if speed_us < MIN_speed_US or speed_us > MAX_speed_US:
                    return simple_response("error", "speed_OUT_OF_RANGE", MIN=MIN_speed_US, MAX=MAX_speed_US)
                
                current_speed_us = speed_us
                stepper_settings['speed'] = speed_us
                print(f"[USB] ACTION: SET speed to {speed_us}µs")
                return simple_response("speed", "OK", SET=speed_us)
            except ValueError:
                return simple_response("error", "INVALID_speed_FORMAT")
        
        # ping - verify slave is online (simple alive check)
        elif cmd == 'ping':
            uptime_ms = utime.ticks_ms() - startup_time
            uptime_s = uptime_ms // 1000
            return simple_response("ping", "OK", UPTIME=f"{uptime_s}s")
        
        # whoami - Device identification
        elif cmd == 'whoami':
            return simple_response("whoami", "OK", DEVICE="stepper", TYPE="motor_controller")
        
        else:
            return simple_response("error", "UNKNOWN_CMD", CMD=cmd)
    
    except Exception as e:
        return f"Error: {e}"

def i2c_irq_handler(i2c_target):
    """Handle I2C target events - DEPRECATED, kept for reference only"""
    pass

# Set up I2C IRQ handlers (disabled - using UART instead)
# slave.irq(i2c_irq_handler)

print("=" * 50)
print(f"MicroPython Version: {sys.version}")
print(f"MicroPython Implementation: {sys.implementation}")
print("=" * 50)

print("[STARTUP] Stepper motor GPIO pins configured")
print(f"[STARTUP]  PUL (Pulse): GPIO {PUL_PIN}")
print(f"[STARTUP]  DIR (Direction): GPIO {DIR_PIN}")
print(f"[STARTUP]  ENA (Enable): GPIO {ENA_PIN}")
print("=" * 50)
print(f"MicroPython Version: {sys.version}")
print(f"MicroPython Implementation: {sys.implementation}")
print("=" * 50)

print("[STARTUP] Stepper motor GPIO pins configured")
print(f"[STARTUP]  PUL (Pulse): GPIO {PUL_PIN}")
print(f"[STARTUP]  DIR (Direction): GPIO {DIR_PIN}")
print(f"[STARTUP]  ENA (Enable): GPIO {ENA_PIN}")
print("[STARTUP] UART slave initialized")
print("[STARTUP] UART command handler configured")
print("[STARTUP] Performing stepper initialization...")
print()

print("=" * 50)
print("[INIT] Starting stepper initialization...")
print("=" * 50)
print("[INIT] Finding home position...")
result = find_home_fast()
if result:
    print("[stepper] Homed to 0° (position: 0°)")
else:
    print("[stepper] WARNING: Home finding failed")
print("[INIT] Initialization complete!")
print("=" * 50)
print()

print("=" * 50)
print("Stepper Motor Pico Firmware - UART REST API Compatible")
print("=" * 50)
print(f"[readY] UART Slave ({device_name}) initialized")
print("[MOTOR] Stepper motor control via pulse/direction/enable")
print(f"[WIRING] PUL/DIR/ENA=GPIO({PUL_PIN}/{DIR_PIN}/{ENA_PIN}), SENSOR=GPIO20")
print()
print("UART Protocol (shared bus with servo and radar):")
print("  Format: stepper:COMMAND[:ARGS]")
print("  Response: stepper:status[:DATA]")
print()
print("Available Commands:")
print("  ping           - Alive check")
print("  status         - Get status (position, state, enabled, calibrated)")
print("  whoami         - Device identification")
print("  spin:<speed>   - Start continuous rotation at speed (µs)")
print("  stop           - Stop continuous rotation")
print("  home           - Find and calibrate home position")
print("  move:<angle>   - Move to absolute angle (0-360°)")
print("  rotate:<delta> - Rotate by relative amount")
print("  speed:<us>     - Set motor speed (pulse duration in µs)")
print("  enable         - Enable motor")
print("  disable        - Disable motor")
print()
print("Examples:")
print("  stepper:ping")
print("  stepper:status")
print("  stepper:spin:2000")
print("  stepper:move:90")
print("  stepper:rotate:45")
print("=" * 50)
print()

# Input buffer for reading commands
pulse_counter = 0  # Count pulses for periodic logging
uart_buffer = b""  # Buffer for reading UART data
last_blink_time = utime.ticks_ms()  # Track LED blink timing
led_state = True  # Current LED state (True = on, False = off)
blink_interval = 500  # 500ms on/off interval for visible blinking

print("[INIT] Starting main loop...")
print()

while True:
    # Blink LED to show we're alive (500ms on, 500ms off)
    current_time = utime.ticks_ms()
    if current_time - last_blink_time >= blink_interval:
        last_blink_time = current_time
        led_state = not led_state
        if led_state:
            led.on()
        else:
            led.off()
    
    # UART polling: Check buffer for commands
    # Check for incoming UART data
    while uart_slaves.any():
        byte = uart_slaves.read(1)
        if byte == b'\n':
            # Complete command received
            cmd_text = uart_buffer.decode().strip()
            uart_buffer = b""
            
            if cmd_text:
                print(f"[UART-RECV] {cmd_text}")
                process_uart_command(cmd_text)
        else:
            uart_buffer += byte
            # Prevent buffer overflow
            if len(uart_buffer) > 256:
                uart_buffer = b""
                send_uart_response("error:buffer_overflow")
    
    # Handle continuous rotation - ALWAYS CHECK AND EXECUTE
    if continuous_rotating and stepper_enabled:
        pulse_motor(current_speed_us)
        
        # Update position based on direction
        if continuous_direction == CW:
            stepper_position = stepper_position + DEGREES_PER_STEP
        else:  # CCW
            stepper_position = stepper_position - DEGREES_PER_STEP
        
        # Keep position in 0-360 range and count revolutions
        if stepper_position >= 360:
            stepper_position = stepper_position - 360
            continuous_revolutions += 1
            print(f"[rotate] Revolution {continuous_revolutions}")
        elif stepper_position < 0:
            stepper_position = stepper_position + 360
            continuous_revolutions += 1
            print(f"[rotate] Revolution {continuous_revolutions}")
        
        # Check if home sensor is triggered
        current_sensor = get_sensor_state()
        if current_sensor == 1 and home_last_state == 0:
            print(f"[SENSOR] home DETECTED at {stepper_position:.1f}° (Rev {continuous_revolutions})")
        home_last_state = current_sensor
        
        stepper_settings['position'] = int(stepper_position)
        
        # Periodic status every 600 pulses
        pulse_counter += 1
        if pulse_counter >= 600:
            pulse_counter = 0
            print(f"[rotate] Position: {stepper_position:.1f}° (Rev: {continuous_revolutions})")
    
    # Check for input via stdin
    try:
        line = sys.stdin.readline()
        if line:
            line = line.strip()
            if line:
                print(f"[STDIN] Received: {line}")
                resp = process_usb_command(line)
                print(f"Result: {resp}")
    except:
        pass
    
    # Short sleep for system responsiveness
    utime.sleep_us(100)
