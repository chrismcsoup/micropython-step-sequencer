# test/test_mycode.py
import sys

# add the dev libs with the unittest module to the python path
sys.path.append("lib-dev")
# also add our src code to the python path
sys.path.append("src")

import unittest
from unittest_helper import create_filtered_test_case
from test_mylib import *
import test_chord_machine

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
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(sys.modules[__name__])
        runner = unittest.TextTestRunner()
        result = runner.run(suite)
        
        # Run MicroPython-compatible tests (test_chord_machine)
        print("\nRunning chord machine tests...")
        chord_success = test_chord_machine.run_tests()
        
        # Exit with error if any tests failed
        if not result.wasSuccessful() or not chord_success:
            sys.exit(1)
