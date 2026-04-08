# Main application for Raspberry Pi Pico Radar and Server Controller
# MicroPython implementation

import machine
import time
import json
from src.servo_controller import ServoController
from src.radar_rcwl0516 import RadarRCWL0516
from src.radar_cqrobot import RadarCQRobot
from src.uart_communication import UARTCommunicationController
from config.settings import *

class RadarServerController:
    def __init__(self):
        print("Initializing Radar Server Controller...")
        
        # Initialize UART communication with Pi4
        self.uart_comm = UARTCommunicationController()
        
        # Initialize servo controller for RC landing gear
        self.servo = ServoController(SERVO_PIN)
        
        # Initialize radar modules based on configuration
        if RADAR_TYPE == "RCWL0516":
            self.radar = RadarRCWL0516(RCWL_PINS)
        elif RADAR_TYPE == "CQROBOT":
            self.radar = RadarCQRobot(CQROBOT_PINS)
        else:
            raise ValueError("Invalid radar type specified")
        
        # Status LED
        self.status_led = machine.Pin(LED_PIN, machine.Pin.OUT)
        
        # System status
        self.is_running = False
        self.radar_active = False
        
        # Initialize UART communication
        self.uart_comm.initialize()
        
        print("Controller initialized successfully")
    
    def start_system(self):
        """Start the radar and servo system"""
        self.is_running = True
        self.status_led.on()
        print("System started")
        
        while self.is_running:
            try:
                # Check for incoming UART messages
                self.uart_comm.check_incoming_messages()
                
                # Get radar readings
                radar_data = self.radar.read_all_sensors()
                
                # Process radar data and control servo
                detection_occurred = self.process_radar_data(radar_data)
                
                # Send radar data to Pi4
                self.uart_comm.send_radar_data(radar_data)
                
                # Send detection alert if motion detected
                if detection_occurred:
                    detection_count = sum(1 for reading in radar_data if reading['detected'])
                    self.uart_comm.send_detection_alert({
                        'detection_count': detection_count,
                        'readings': radar_data,
                        'servo_activated': self.radar_active
                    })
                
                # Process outgoing UART messages
                self.uart_comm.process_outgoing_messages()
                
                # Small delay to prevent overwhelming the system
                time.sleep_ms(SCAN_INTERVAL_MS)
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep_ms(1000)
    
    def process_radar_data(self, radar_data):
        """Process radar readings and control servo accordingly"""
        detection_count = sum(1 for reading in radar_data if reading['detected'])
        detection_occurred = False
        
        if detection_count > DETECTION_THRESHOLD:
            if not self.radar_active:
                print(f"Motion detected on {detection_count} sensors")
                self.activate_servo()
                self.radar_active = True
                detection_occurred = True
        else:
            if self.radar_active:
                print("No motion detected - deactivating")
                self.deactivate_servo()
                self.radar_active = False
        
        return detection_occurred
    
    def activate_servo(self):
        """Activate the RC landing gear servo"""
        self.servo.set_position(SERVO_ACTIVE_POSITION)
        self.uart_comm.send_servo_status(SERVO_ACTIVE_POSITION, True)
        print("Servo activated")
    
    def deactivate_servo(self):
        """Deactivate the RC landing gear servo"""
        self.servo.set_position(SERVO_NEUTRAL_POSITION)
        self.uart_comm.send_servo_status(SERVO_NEUTRAL_POSITION, False)
        print("Servo deactivated")
    
    def stop_system(self):
        """Stop the system gracefully"""
        self.is_running = False
        
        # Send final status to Pi4
        self.uart_comm.send_system_info()
        
        # Stop components
        self.servo.stop()
        self.uart_comm.stop()
        self.status_led.off()
        
        print("System stopped")

def main():
    """Main entry point"""
    try:
        controller = RadarServerController()
        controller.start_system()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
        if 'controller' in locals():
            controller.stop_system()
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    main()