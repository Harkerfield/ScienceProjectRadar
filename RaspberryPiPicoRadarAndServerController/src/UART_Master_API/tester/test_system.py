# Test utilities for Raspberry Pi Pico Radar Controller
# MicroPython implementation

import time
from config.settings import *
from src.servo_controller import ServoController
from src.radar_rcwl0516 import RadarRCWL0516
from src.radar_cqrobot import RadarCQRobot

def test_servo():
    """Test servo controller functionality"""
    print("=== Servo Controller Test ===")
    
    try:
        servo = ServoController(SERVO_PIN)
        
        print("Testing servo positions...")
        positions = [0, 45, 90, 135, 180, 90]  # End at neutral
        
        for pos in positions:
            print(f"Moving to {pos} degrees...")
            servo.set_position(pos)
            time.sleep_ms(1000)
        
        print("Testing servo sweep...")
        servo.sweep(0, 180, 10, 100)
        servo.sweep(180, 0, 10, 100)
        
        print("Centering servo...")
        servo.center()
        time.sleep_ms(1000)
        
        servo.stop()
        print("Servo test completed successfully")
        return True
        
    except Exception as e:
        print(f"Servo test failed: {e}")
        return False

def test_rcwl_radar():
    """Test RCWL-0516 radar sensors"""
    print("=== RCWL-0516 Radar Test ===")
    
    try:
        radar = RadarRCWL0516(RCWL_PINS)
        
        print("Calibrating sensors (keep area clear)...")
        calibration_data = radar.calibrate_sensors(5000)  # 5 second calibration
        
        print("\nTesting sensor readings...")
        radar.test_all_sensors()
        
        print("\nWaiting for motion detection (30 seconds)...")
        detection = radar.wait_for_detection(30000)
        
        if detection:
            print(f"Motion detected on sensor {detection['sensor_id']}")
        else:
            print("No motion detected during test period")
        
        print("RCWL radar test completed")
        return True
        
    except Exception as e:
        print(f"RCWL radar test failed: {e}")
        return False

def test_cqrobot_radar():
    """Test CQRobot radar modules"""
    print("=== CQRobot Radar Test ===")
    
    try:
        radar = RadarCQRobot(CQROBOT_PINS)
        
        print("Testing all modules...")
        radar.test_all_modules()
        
        print("\nGetting module status...")
        for i in range(len(radar.modules)):
            status = radar.get_module_status(i)
            print(f"Module {status['name']}:")
            print(f"  Detection count: {status['detection_count']}")
            print(f"  Average distance: {status['average_distance']:.1f}cm")
            print(f"  Average velocity: {status['average_velocity']:.1f}cm/s")
        
        print("CQRobot radar test completed")
        return True
        
    except Exception as e:
        print(f"CQRobot radar test failed: {e}")
        return False

def test_system_integration():
    """Test complete system integration"""
    print("=== System Integration Test ===")
    
    try:
        # Import main controller
        from RaspberryPiPicoRadarAndServerController.src.UART_Slave_Radar.tester.main import RadarServerController
        
        print("Initializing radar server controller...")
        controller = RadarServerController()
        
        print("Testing servo activation...")
        controller.activate_servo()
        time.sleep_ms(2000)
        
        print("Testing servo deactivation...")
        controller.deactivate_servo()
        time.sleep_ms(2000)
        
        print("Testing radar reading...")
        if RADAR_TYPE == "RCWL0516":
            radar_data = controller.radar.read_all_sensors()
            print(f"RCWL sensors read: {len(radar_data)} readings")
        elif RADAR_TYPE == "CQROBOT":
            radar_data = controller.radar.read_all_sensors()
            print(f"CQRobot modules read: {len(radar_data)} readings")
        
        print("Testing detection processing...")
        controller.process_radar_data(radar_data)
        
        controller.stop_system()
        print("System integration test completed")
        return True
        
    except Exception as e:
        print(f"System integration test failed: {e}")
        return False

def run_performance_test():
    """Run performance benchmarks"""
    print("=== Performance Test ===")
    
    try:
        from RaspberryPiPicoRadarAndServerController.src.UART_Slave_Radar.tester.main import RadarServerController
        
        controller = RadarServerController()
        
        # Timing tests
        iterations = 100
        start_time = time.ticks_ms()
        
        for i in range(iterations):
            radar_data = controller.radar.read_all_sensors()
            controller.process_radar_data(radar_data)
            
            if i % 10 == 0:
                print(f"Completed {i}/{iterations} iterations")
        
        end_time = time.ticks_ms()
        total_time = time.ticks_diff(end_time, start_time)
        avg_time_per_cycle = total_time / iterations
        
        print(f"\nPerformance Results:")
        print(f"Total time: {total_time}ms")
        print(f"Average time per cycle: {avg_time_per_cycle:.2f}ms")
        print(f"Theoretical max frequency: {1000/avg_time_per_cycle:.1f} Hz")
        
        controller.stop_system()
        return True
        
    except Exception as e:
        print(f"Performance test failed: {e}")
        return False

def run_all_tests():
    """Run all test suites"""
    print("========================================")
    print("Raspberry Pi Pico Radar Controller Tests")
    print("========================================\n")
    
    # Print configuration
    print_configuration()
    print()
    
    # Validate configuration
    config_errors = validate_configuration()
    if config_errors:
        print("Configuration Errors:")
        for error in config_errors:
            print(f"  - {error}")
        print("\nPlease fix configuration errors before running tests")
        return False
    
    test_results = {}
    
    # Test servo
    print("1. Testing Servo Controller...")
    test_results['servo'] = test_servo()
    print()
    
    # Test radar based on configuration
    if RADAR_TYPE == "RCWL0516":
        print("2. Testing RCWL-0516 Radar...")
        test_results['radar'] = test_rcwl_radar()
    elif RADAR_TYPE == "CQROBOT":
        print("2. Testing CQRobot Radar...")
        test_results['radar'] = test_cqrobot_radar()
    print()
    
    # Test system integration
    print("3. Testing System Integration...")
    test_results['integration'] = test_system_integration()
    print()
    
    # Test performance
    print("4. Testing Performance...")
    test_results['performance'] = run_performance_test()
    print()
    
    # Print test summary
    print("========================================")
    print("Test Summary:")
    print("========================================")
    
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        print(f"{test_name.capitalize()}: {status}")
    
    all_passed = all(test_results.values())
    overall_status = "ALL TESTS PASSED" if all_passed else "SOME TESTS FAILED"
    print(f"\nOverall Result: {overall_status}")
    
    return all_passed

def main():
    """Main test function"""
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test suite error: {e}")

if __name__ == "__main__":
    main()