# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import sys
import unittest
import logging.config


# When True it will run the integrated tests
TEST_FULL = False

# TEST_FULL flag
TEST_FULL_FLAG = "-cc"

# Set up logging settings during testing
logging_format = "[%(levelname)s - %(name)s] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=logging_format)

# Disable logging during testing
logging.disable(logging.CRITICAL)

# Automatically set TEST_FULL
if TEST_FULL_FLAG in sys.argv: TEST_FULL = True

# Disable the max output size during unittesting
unittest.TestCase.maxDiff = None
