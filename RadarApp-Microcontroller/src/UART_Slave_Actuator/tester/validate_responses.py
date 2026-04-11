"""
Response Generation Validation Test
Run this on each slave Pico to verify json_response() works correctly
This tests the EXACT json_response function end-to-end
"""

# Test data
test_cases = [
    ("PING response", {"s": "ok", "msg": "alive", "addr": "0x12"}),
    ("OPEN response", {"s": "ok", "msg": "opened", "pos": 100, "state": "open"}),
    ("STATUS response", {"s": "ok", "pos": 50, "state": "moving", "moving": 1}),
    ("Error response", {"s": "error", "msg": "unknown_command"}),
]

def validate_json_response():
    """Test json_response function"""
    print("\n" + "="*70)
    print("JSON Response Validation Test")
    print("="*70)
    
    # Import the function from main
    try:
        from src.i2c_Slave_Stepper.main import json_response
        device_name = "Stepper (0x10)"
    except:
        try:
            from src.i2c_Slave_Actuator.main import json_response
            device_name = "Actuator (0x12)"
        except Exception as import_err:
            print(f"[ERROR] Could not import json_response: {import_err}")
            print("[ERROR] Make sure this script is run from the device directory")
            return False
    
    print(f"[OK] Loaded json_response from {device_name}")
    print()
    
    passed = 0
    failed = 0
    
    # Test 1: Basic response generation
    print("Test 1: Basic PING Response")
    print("-" * 40)
    try:
        resp = json_response("ok", msg="alive", addr="0x12")
        print(f"  Result type: {type(resp)}")
        print(f"  Result: {resp}")
        
        # Should be a string
        if isinstance(resp, str):
            print(f"  ✅ Response is string")
            passed += 1
        else:
            print(f"  ❌ Response is not string!")
            failed += 1
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        failed += 1
    print()
    
    # Test 2: Encode to bytes
    print("Test 2: Encode Response to Bytes")
    print("-" * 40)
    try:
        resp = json_response("ok", msg="alive", addr="0x12")
        resp_bytes = resp.encode()
        print(f"  String: {resp}")
        print(f"  Encoded type: {type(resp_bytes)}")
        print(f"  Bytes length: {len(resp_bytes)}")
        print(f"  Bytes: {resp_bytes}")
        
        if isinstance(resp_bytes, bytes):
            print(f"  ✅ Encoded to bytes successfully")
            passed += 1
        else:
            print(f"  ❌ Encode failed!")
            failed += 1
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        failed += 1
    print()
    
    # Test 3: Various response types
    print("Test 3: Different Response Types")
    print("-" * 40)
    
    responses = [
        ("Simple status", json_response("ok")),
        ("With strings", json_response("ok", msg="test", device="actuator")),
        ("With numbers", json_response("ok", pos=42, speed=1000)),
        ("With booleans", json_response("ok", moving=1, enabled=0)),
        ("Error response", json_response("error", msg="bad_command")),
    ]
    
    for name, resp in responses:
        try:
            print(f"  {name}:")
            print(f"    {resp}")
            resp_bytes = resp.encode()
            print(f"    → {len(resp_bytes)} bytes")
            passed += 1
        except Exception as e:
            print(f"    ❌ Error: {e}")
            failed += 1
    print()
    
    # Test 4: Buffer write simulation
    print("Test 4: Buffer Write Simulation")
    print("-" * 40)
    try:
        # Create a buffer like I2CTarget would
        i2c_mem = bytearray(256)
        
        # Get response
        resp = json_response("ok", msg="alive", addr="0x12")
        resp_bytes = resp.encode()
        
        print(f"  Response: {resp_bytes}")
        print(f"  Length: {len(resp_bytes)}")
        
        # Clear buffer
        for idx in range(256):
            i2c_mem[idx] = 0
        
        # Write response
        for idx in range(len(resp_bytes)):
            i2c_mem[idx] = resp_bytes[idx]
        
        # Verify
        verify = bytes(i2c_mem[:len(resp_bytes)])
        print(f"  Written: {verify}")
        
        if verify == resp_bytes:
            print(f"  ✅ Buffer write successful")
            passed += 1
        else:
            print(f"  ❌ Buffer write mismatch!")
            print(f"     Expected: {resp_bytes}")
            print(f"     Got: {verify}")
            failed += 1
    except Exception as e:
        print(f"  ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    print()
    
    # Summary
    print("="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED - Response generation working correctly!")
    else:
        print(f"❌ {failed} test(s) failed - Check errors above")
    
    return failed == 0

def test_json_parsing():
    """Verify generated JSON can be parsed"""
    print("\n" + "="*70)
    print("JSON Parsing Validation")
    print("="*70)
    
    try:
        import json as json_lib
    except:
        print("[SKIP] json module not available")
        return
    
    try:
        from src.i2c_Slave_Stepper.main import json_response
    except:
        try:
            from src.i2c_Slave_Actuator.main import json_response
        except:
            print("[SKIP] Could not import json_response")
            return
    
    test_cases = [
        ("PING", json_response("ok", msg="alive", addr="0x12")),
        ("OPEN", json_response("ok", msg="opened", pos=100, state="open")),
        ("ERROR", json_response("error", msg="unknown_command")),
    ]
    
    for name, resp_str in test_cases:
        try:
            print(f"\nParsing: {name}")
            print(f"  String: {resp_str}")
            parsed = json_lib.loads(resp_str)
            print(f"  Parsed: {parsed}")
            print(f"  ✅ JSON valid")
        except Exception as e:
            print(f"  ❌ Parse error: {e}")

if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("* Response Generation Validation Test")
    print("* Run this on each Slave Pico to verify response pipeline")
    print("*" * 70)
    
    success = validate_json_response()
    test_json_parsing()
    
    if success:
        print("\n✅ Device is ready - responses should work correctly")
    else:
        print("\n❌ Device has issues - check logs above")
