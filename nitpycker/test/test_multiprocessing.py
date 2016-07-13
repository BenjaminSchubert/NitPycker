#!/usr/bin/env python3

"""
Tests specifics to the use of multiprocessing for NitPycker
"""


import unittest

from nitpycker.runner import ParallelRunner
from nitpycker.test import NUMBER_OF_PROCESS, run_tests


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class MultiprocessingTests(unittest.TestCase):
    """
    Tests related to the multiprocessing part of the framework
    """
    def check_error(self, string, output, result):
        if string not in output:  # pragma: nocover
            self.fail("An error occurred: \n{}".format(output.replace("\n", "\n\t")))

        self.assertTrue(result)

    def test_isolation(self):
        result, output = run_tests(
            "check_isolation.py", test_runner=ParallelRunner, process_number=NUMBER_OF_PROCESS)

        self.check_error("OK", output, result)

    def test_no_parallel_class(self):
        result, output = run_tests(
            "check_class_no_parallel.py", test_runner=ParallelRunner, process_number=NUMBER_OF_PROCESS)

        self.check_error("OK", output, result)

    def test_no_parallel_module(self):
        result, output = run_tests(
            "check_module_no_parallel.py", test_runner=ParallelRunner, process_number=NUMBER_OF_PROCESS)

        self.check_error("OK", output, result)


if __name__ == "__main__":
    unittest.main()
