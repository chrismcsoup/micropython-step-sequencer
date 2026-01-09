# test/run_tests.py
import sys

# add the dev libs with the unittest module to the python path
sys.path.append("lib-dev")
# also add our src code to the python path
sys.path.append("src")

import unittest
from unittest_helper import create_filtered_test_case
from test_mylib import TestMyLib
import test_chord_machine


def run_unittest_tests():
    """Run unittest-based tests in a MicroPython-compatible way."""
    test_classes = [TestMyLib]
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        instance = test_class()
        
        for method_name in dir(instance):
            if method_name.startswith("test_"):
                try:
                    method = getattr(instance, method_name)
                    method()
                    print("  [OK] " + method_name)
                    passed += 1
                except AssertionError as e:
                    print("  [FAIL] " + method_name + ": " + str(e))
                    failed += 1
                except Exception as e:
                    print("  [ERROR] " + method_name + ": " + str(e))
                    failed += 1
    
    print("Results: " + str(passed) + " passed, " + str(failed) + " failed")
    return failed == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run a specific test case class or test method in a specific test case class
        test_path = sys.argv[1]
        _TestClass = create_filtered_test_case(test_path)
        suite = unittest.TestSuite()
        suite.addTest(_TestClass())
        runner = unittest.TextTestRunner()
        runner.run(suite)
    else:
        # Run unittest tests (test_mylib)
        print("Running unittest tests...")
        mylib_success = run_unittest_tests()
        
        # Run MicroPython-compatible tests (test_chord_machine)
        print("\nRunning chord machine tests...")
        chord_success = test_chord_machine.run_tests()
        
        # Exit with error if any tests failed
        if not mylib_success or not chord_success:
            sys.exit(1)
