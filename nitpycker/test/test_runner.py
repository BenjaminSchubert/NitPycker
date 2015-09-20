#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main integration tests for NitPycker
"""

import unittest
import re
import collections

from nitpycker.plugins.manager import Manager
from nitpycker.runners import ParallelRunner
from nitpycker.test import NUMBER_OF_PROCESS, run_tests

__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class MainTest(unittest.TestCase):
    def check_output(self, _unittest, nitpycker):
        regex_time_spent = r'Ran \d+ tests in \d+\.\d+s'
        unittest_time = re.search(regex_time_spent, _unittest)
        nitpycker_time = re.search(regex_time_spent, nitpycker)

        self.assertEqual(
            unittest_time.group(0).split(" ")[1], nitpycker_time.group(0).split(" ")[1],
            msg="The number of tests ran by unittest and NitPycker is not the same"
        )

        _unittest = _unittest[:unittest_time.start()] + _unittest[unittest_time.end():]
        nitpycker = nitpycker[:nitpycker_time.start()] + nitpycker[nitpycker_time.end():]

        nitpycker = re.sub(r'=+\nUNEXPECTED SUCCESS:.*\n-+\nThis test passed and it shouldn\'t have\n', "", nitpycker)

        unittest_results, unittest_output = _unittest.split("\n", 1)
        nitpycker_results, nitpycker_output = nitpycker.split("\n", 1)
        self.assertEqual(collections.Counter(unittest_results), collections.Counter(nitpycker_results))
        self.assertEqual(unittest_output, nitpycker_output)

    def test_against_unittest(self):
        test_pattern = "check_against_unittest.py"
        self.maxDiff = None

        unittest_output = run_tests(test_pattern)
        nitpycker_output = run_tests(
            test_pattern, test_runner=ParallelRunner,
            plugins_manager=Manager(), process_number=NUMBER_OF_PROCESS, verbosity=1
        )

        self.check_output(unittest_output, nitpycker_output)

    def test_isolation(self):
        nitpycker_output = run_tests(
            "check_isolation.py", test_runner=ParallelRunner,
            plugins_manager=Manager(), process_number=NUMBER_OF_PROCESS, verbosity=1
        )

        self.assertIn("OK", nitpycker_output, msg="An error occurred while running : \n{}".format(nitpycker_output))


if __name__ == "__main__":
    unittest.main()
