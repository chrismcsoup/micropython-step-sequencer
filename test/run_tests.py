# test/test_mycode.py
import sys

# add the dev libs with the unittest module to the python path
sys.path.append("lib-dev")
# also add our src code to the python path
sys.path.append("src")

import unittest
from unittest_helper import create_filtered_test_case
from test_mylib import *

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
        unittest.main()
