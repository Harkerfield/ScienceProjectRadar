# Configuration settings for Raspberry Pi Pico Radar and Server Controller
# MicroPython implementation

# System Configuration
SCAN_INTERVAL_MS = 100  # Milliseconds between radar scans
DETECTION_THRESHOLD = 1  # Minimum number of sensors that must detect motion
LED_PIN = 25  # Built-in LED pin on Pico

# UART Communication with Raspberry Pi 4
UART_TO_PI4_ID = 1  # UART1 for communication with Pi4
UART_TO_PI4_TX = 8  # GPIO 8 for TX to Pi4
UART_TO_PI4_RX = 9  # GPIO 9 for RX from Pi4
UART_TO_PI4_BAUDRATE = 115200  # Baud rate for Pi4 communication
UART_DATA_INTERVAL_MS = 250  # Send data to Pi4 every 250ms

# Servo Configuration
servo_PIN = 16  # GPIO pin for servo control
servo_NEUTRAL_POSITION = 90  # Neutral position in degrees
servo_ACTIVE_POSITION = 45   # Active position in degrees
servo_FREQUENCY = 50  # PWM frequency for servo (50Hz standard)

# Radar Type Configuration - Choose one
RADAR_TYPE = "RCWL0516"  # Options: "RCWL0516" or "CQROBOT"

# RCWL-0516 Configuration (if using RCWL-0516 modules)
RCWL_PINS = [2, 3, 4, 5, 6, 7, 8, 9]  # GPIO pins for 8 RCWL-0516 modules

# CQRobot 10.525GHz Module Configuration (if using CQRobot modules)
CQROBOT_PINS = {
    'modules': [
        {
            'uart_id': 0,
            'tx_pin': 0,
            'rx_pin': 1,
            'name': 'radar_module_1'
        },
        {
            'uart_id': 1,
            'tx_pin': 4,
            'rx_pin': 5,
            'name': 'radar_module_2'
        }
    ]
}

# CQRobot Module Parameters
CQROBOT_SENSITIVITY = 75  # Detection sensitivity (0-100)
CQROBOT_MAX_DISTANCE = 300  # Maximum detection distance in cm
CQROBOT_BAUDRATE = 115200  # UART baud rate

# Detection Parameters
MOTION_TIMEOUT_MS = 5000  # Time in ms before deactivating after no detection
CALIBRATION_TIME_MS = 10000  # Calibration period in milliseconds

# System Timing
STARTUP_DELAY_MS = 2000  # Delay before starting main operation
SHUTDOWN_DELAY_MS = 1000  # Delay during shutdown

# Debug Configuration
DEBUG_MODE = True  # Enable debug output
VERBOSE_LOGGING = False  # Enable verbose logging

# Pin Assignments Summary
PIN_ASSIGNMENTS = {
    'servo': servo_PIN,
    'status_led': LED_PIN,
    'rcwl_sensors': RCWL_PINS,
    'cqrobot_uart0_tx': CQROBOT_PINS['modules'][0]['tx_pin'],
    'cqrobot_uart0_rx': CQROBOT_PINS['modules'][0]['rx_pin'],
    'cqrobot_uart1_tx': CQROBOT_PINS['modules'][1]['tx_pin'],
    'cqrobot_uart1_rx': CQROBOT_PINS['modules'][1]['rx_pin'],
    'pi4_uart_tx': UART_TO_PI4_TX,
    'pi4_uart_rx': UART_TO_PI4_RX
}

def print_configuration():
    """Print current configuration for debugging"""
    print("=== Radar Controller Configuration ===")
    print(f"Radar Type: {RADAR_TYPE}")
    print(f"Servo Pin: {servo_PIN}")
    print(f"Scan Interval: {SCAN_INTERVAL_MS}ms")
    print(f"Detection Threshold: {DETECTION_THRESHOLD}")
    
    if RADAR_TYPE == "RCWL0516":
        print(f"RCWL-0516 Pins: {RCWL_PINS}")
    elif RADAR_TYPE == "CQROBOT":
        print("CQRobot Modules:")
        for module in CQROBOT_PINS['modules']:
            print(f"  {module['name']}: UART{module['uart_id']} (TX:{module['tx_pin']}, RX:{module['rx_pin']})")
    
    print("=====================================")

def validate_configuration():
    """Validate configuration settings"""
    errors = []
    
    # Check radar type
    if RADAR_TYPE not in ["RCWL0516", "CQROBOT"]:
        errors.append(f"Invalid RADAR_TYPE: {RADAR_TYPE}")
    
    # Check servo configuration
    if not (0 <= servo_PIN <= 28):
        errors.append(f"Invalid servo_PIN: {servo_PIN}")
    
    if not (0 <= servo_NEUTRAL_POSITION <= 180):
        errors.append(f"Invalid servo_NEUTRAL_POSITION: {servo_NEUTRAL_POSITION}")
    
    if not (0 <= servo_ACTIVE_POSITION <= 180):
        errors.append(f"Invalid servo_ACTIVE_POSITION: {servo_ACTIVE_POSITION}")
    
    # Check RCWL pins
    if RADAR_TYPE == "RCWL0516":
        for pin in RCWL_PINS:
            if not (0 <= pin <= 28):
                errors.append(f"Invalid RCWL pin: {pin}")
    
    # Check CQRobot configuration
    if RADAR_TYPE == "CQROBOT":
        for module in CQROBOT_PINS['modules']:
            if not (0 <= module['uart_id'] <= 1):
                errors.append(f"Invalid UART ID for {module['name']}: {module['uart_id']}")
            
            if not (0 <= module['tx_pin'] <= 28):
                errors.append(f"Invalid TX pin for {module['name']}: {module['tx_pin']}")
            
            if not (0 <= module['rx_pin'] <= 28):
                errors.append(f"Invalid RX pin for {module['name']}: {module['rx_pin']}")
    
    # Check timing parameters
    if SCAN_INTERVAL_MS < 10:
        errors.append("SCAN_INTERVAL_MS too low (minimum 10ms)")
    
    if DETECTION_THRESHOLD < 1:
        errors.append("DETECTION_THRESHOLD must be at least 1")
    
    return errors

# Alternative configurations for different setups
ALTERNATIVE_CONFIGS = {
    'minimal_rcwl': {
        'RADAR_TYPE': 'RCWL0516',
        'RCWL_PINS': [2, 3, 4, 5],  # Only 4 sensors
        'DETECTION_THRESHOLD': 1
    },
    'dual_cqrobot': {
        'RADAR_TYPE': 'CQROBOT',
        'CQROBOT_PINS': {
            'modules': [
                {'uart_id': 0, 'tx_pin': 0, 'rx_pin': 1, 'name': 'front_radar'},
                {'uart_id': 1, 'tx_pin': 4, 'rx_pin': 5, 'name': 'rear_radar'}
            ]
        }
    },
    'single_cqrobot': {
        'RADAR_TYPE': 'CQROBOT',
        'CQROBOT_PINS': {
            'modules': [
                {'uart_id': 0, 'tx_pin': 0, 'rx_pin': 1, 'name': 'main_radar'}
            ]
        }
    }
}

def load_alternative_config(config_name):
    """Load an alternative configuration"""
    if config_name in ALTERNATIVE_CONFIGS:
        config = ALTERNATIVE_CONFIGS[config_name]
        globals().update(config)
        print(f"Loaded alternative configuration: {config_name}")
        return True
    else:
        print(f"Unknown configuration: {config_name}")
        return False