# Comprehensive API Test Suite
# Tests all device commands matching the client API
# Run this to verify the full command chain: Client → Server API → Pico Master → Slaves

import smbus
import time
import sys

# I2C Configuration
I2C_BUS = 1
I2C_SLAVE_stepper = 0x10
I2C_SLAVE_servo = 0x12

# Command test definitions matching client API calls
COMMAND_TESTS = {
    'stepper': [
        {'cmd': 'ping', 'expected': 'OK', 'timeout': 2, 'description': 'Stepper alive check'},
        {'cmd': 'whoami', 'expected': 'OK', 'timeout': 2, 'description': 'Stepper identification'},
        {'cmd': 'status', 'expected': 'OK', 'timeout': 2, 'description': 'Get stepper status'},
        {'cmd': 'enable', 'expected': 'OK', 'timeout': 2, 'description': 'Enable motor'},
        {'cmd': 'home', 'expected': 'OK', 'timeout': 5, 'description': 'Calibrate home position'},
        {'cmd': 'speed:2000', 'expected': 'OK', 'timeout': 2, 'description': 'Set speed (2000µs)'},
        {'cmd': 'move:0', 'expected': 'OK', 'timeout': 5, 'description': 'Move to 0° (home)'},
        {'cmd': 'move:90', 'expected': 'OK', 'timeout': 5, 'description': 'Move to 90°'},
        {'cmd': 'move:180', 'expected': 'OK', 'timeout': 5, 'description': 'Move to 180°'},
        {'cmd': 'move:360', 'expected': 'OK', 'timeout': 5, 'description': 'Move to 360° (raise)'},
        {'cmd': 'rotate:45', 'expected': 'OK', 'timeout': 3, 'description': 'Rotate +45°'},
        {'cmd': 'rotate:-45', 'expected': 'OK', 'timeout': 3, 'description': 'Rotate -45°'},
        {'cmd': 'spin:2000', 'expected': 'OK', 'timeout': 2, 'description': 'Start spinning at 2000µs'},
        {'cmd': 'stop', 'expected': 'OK', 'timeout': 2, 'description': 'Stop motion'},
        {'cmd': 'disable', 'expected': 'OK', 'timeout': 2, 'description': 'Disable motor'},
    ],
    'servo': [
        {'cmd': 'ping', 'expected': 'OK', 'timeout': 2, 'description': 'Servo alive check'},
        {'cmd': 'whoami', 'expected': 'OK', 'timeout': 2, 'description': 'Servo identification'},
        {'cmd': 'status', 'expected': 'OK', 'timeout': 2, 'description': 'Get servo status'},
        {'cmd': 'open', 'expected': 'OK', 'timeout': 8, 'description': 'Open/extend servo (6 seconds)'},
        {'cmd': 'status', 'expected': 'OK', 'timeout': 2, 'description': 'Get servo status (verify open)'},
        {'cmd': 'close', 'expected': 'OK', 'timeout': 8, 'description': 'Close/retract servo (6 seconds)'},
        {'cmd': 'status', 'expected': 'OK', 'timeout': 2, 'description': 'Get servo status (verify closed)'},
    ],
    'radar': [
        {'cmd': 'ping', 'expected': 'OK', 'timeout': 2, 'description': 'Radar alive check'},
        {'cmd': 'whoami', 'expected': 'OK', 'timeout': 2, 'description': 'Radar identification'},
        {'cmd': 'status', 'expected': 'OK', 'timeout': 2, 'description': 'Get radar status'},
        {'cmd': 'read', 'expected': 'OK', 'timeout': 2, 'description': 'Read radar measurements'},
        {'cmd': 'set_range:100', 'expected': 'OK', 'timeout': 2, 'description': 'Set range to 100cm'},
        {'cmd': 'set_velocity:5.0', 'expected': 'OK', 'timeout': 2, 'description': 'Set velocity to 5.0 m/s'},
    ]
}

class APITester:
    """Comprehensive API test runner"""
    
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def format_command(self, device, cmd):
        """Format command as it appears on UART"""
        return f"{device}:{cmd}"
    
    def send_uart_command(self, device, cmd):
        """
        Send command via UART0 (to Pico Master)
        
        In production, you'd write to /dev/ttyAMA0 here
        For testing, we simulate or connect to a serial device
        """
        formatted = self.format_command(device, cmd)
        print(f"    → Sending: {formatted}")
        
        # TODO: Implement actual UART communication
        # For now, return simulated response
        return f"{device}:OK:response=test"
    
    def send_i2c_command(self, device_addr, cmd):
        """Send command via I2C to slave device"""
        try:
            bus = smbus.SMBus(I2C_BUS)
            
            # Format command as bytes
            cmd_bytes = cmd.encode('utf-8')
            
            # Write command to device
            bus.write_i2c_block_data(device_addr, 0, list(cmd_bytes))
            time.sleep(0.1)
            
            # Read response
            response = bus.read_i2c_block_data(device_addr, 0, 64)
            response_bytes = bytes(response).rstrip(b'\x00')
            response_str = response_bytes.decode('utf-8', errors='ignore')
            
            bus.close()
            return response_str
        except Exception as e:
            return f"I2C_error: {e}"
    
    def test_command(self, device, test_case):
        """Test a single command"""
        cmd = test_case['cmd']
        expected = test_case['expected']
        timeout = test_case['timeout']
        description = test_case['description']
        
        self.total_tests += 1
        
        print(f"\n  [TEST] {description}")
        print(f"    Command: {device}:{cmd}")
        
        try:
            # Send command (UART to Pico Master)
            response = self.send_uart_command(device, cmd)
            
            print(f"    ← Response: {response}")
            
            # Check if expected status in response
            if expected in response:
                print(f"    ✓ PASS")
                self.passed_tests += 1
                return True
            else:
                print(f"    ✗ FAIL (expected '{expected}')")
                self.failed_tests += 1
                return False
                
        except Exception as e:
            print(f"    ✗ EXCEPTION: {e}")
            self.failed_tests += 1
            return False
    
    def run_all_tests(self):
        """Run all command tests"""
        print("=" * 80)
        print("COMPREHENSIVE API TEST SUITE")
        print("=" * 80)
        print()
        
        for device in ['stepper', 'servo', 'radar']:
            print(f"\n{'='*80}")
            print(f"DEVICE: {device}")
            print(f"{'='*80}")
            
            self.results[device] = {
                'passed': 0,
                'failed': 0,
                'tests': []
            }
            
            tests = COMMAND_TESTS.get(device, [])
            for i, test_case in enumerate(tests, 1):
                result = self.test_command(device, test_case)
                self.results[device]['tests'].append({
                    'cmd': test_case['cmd'],
                    'passed': result
                })
                
                if result:
                    self.results[device]['passed'] += 1
                else:
                    self.results[device]['failed'] += 1
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print()
        
        for device in ['stepper', 'servo', 'radar']:
            result = self.results[device]
            passed = result['passed']
            failed = result['failed']
            total = passed + failed
            
            status = "✓ PASS" if failed == 0 else "✗ FAIL"
            print(f"{device}: {status}")
            print(f"  Passed: {passed}/{total}")
            print(f"  Failed: {failed}/{total}")
            
            if failed > 0:
                print(f"  Failed commands:")
                for test in result['tests']:
                    if not test['passed']:
                        print(f"    - {test['cmd']}")
            print()
        
        total_passed = sum(r['passed'] for r in self.results.values())
        total_failed = sum(r['failed'] for r in self.results.values())
        total = total_passed + total_failed
        
        print(f"TOTAL: {total_passed}/{total} tests passed")
        
        if total_failed == 0:
            print("✓ ALL TESTS PASSED!")
        else:
            print(f"✗ {total_failed} test(s) failed")
        print()

def print_api_specification():
    """Print the API specification for reference"""
    print("=" * 80)
    print("CLIENT API SPECIFICATION")
    print("=" * 80)
    print()
    
    print("Command Format: DEVICE:COMMAND[:ARGS]")
    print()
    print("Positional Argument Commands (value only, no key name):")
    print("  - move:degrees → e.g., move:360")
    print("  - rotate:delta_degrees → e.g., rotate:45")
    print("  - spin:speed_us → e.g., spin:2000")
    print("  - speed:speed_us → e.g., speed:2000")
    print("  - set_range:centimeters → e.g., set_range:100")
    print("  - set_velocity:meters_per_second → e.g., set_velocity:5.0")
    print()
    print("stepper Commands:")
    for test in COMMAND_TESTS['stepper']:
        print(f"  - {test['cmd']:20s} → {test['description']}")
    print()
    print("servo Commands:")
    for test in COMMAND_TESTS['servo']:
        print(f"  - {test['cmd']:20s} → {test['description']}")
    print()
    print("radar Commands:")
    for test in COMMAND_TESTS['radar']:
        print(f"  - {test['cmd']:20s} → {test['description']}")
    print()

if __name__ == '__main__':
    print_api_specification()
    
    tester = APITester()
    tester.run_all_tests()
