#!/usr/bin/env python3

"""
Tests to check that the output of NitPycker is the same as the one
of unittest in cases where no multiprocessing is involved
"""

import os
import re
import unittest
import warnings

from nitpycker.runner import ParallelRunner, SerializationWarning
from nitpycker.test import run_tests


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


test_modules = [
    "check_tests_incomes.py",
    "check_class_no_parallel.py",
    "check_module_no_parallel.py",
    "check_module_import_failure.py",
    "check_non_serializable.py",
    "check_tests_with_multiprocessing.py"
]

test_args = [
    {"verbosity": 0},
    {"verbosity": 1},
    {"verbosity": 2},
]


def get_function_name(file, kwargs):
    """
    given a file and the arguments of the program, this will create a meaningful name
    for the test function

    :param file: name of file in which to find the tests
    :param kwargs: arguments to pass to the test runner
    :return: name of the function to use
    """
    return "test_{}{}".format(
            os.path.splitext(file)[0].replace("check_", ""),
            "_" + "_".join(["{}_{}".format(key, value) for key, value in kwargs.items()] if len(kwargs) else "")
        ).strip("_")


def set_function(cls, function_name, func):
    """
    adds a new function to the given class with the given name

    :param cls: class to which to add the function
    :param function_name: name of the function to set
    :param func: function to attach
    """
    setattr(cls, function_name, func)
    setattr(getattr(UnittestComparisonTest, function_name), "__name__", function_name)


class UnittestComparisonTest(unittest.TestCase):
    """
    Tests both unittest and nitpycker results and makes sure
    that they both match on simple test cases
    """
    def compare_outputs(self, unittest_output, nitpycker_output):
        """
        Compare both unittest and nitpycker output for anomalies

        :param unittest_output: output gained from unittest
        :param nitpycker_output: output gained from nitpycker
        """
        in1 = unittest_output - nitpycker_output
        in2 = nitpycker_output - unittest_output

        if any([in1, in2]):  # pragma: nocover
            err_message = "The two outputs are not the same:\n"

            if in1:
                err_message += "\tItems from unittest but not in nitpycker:\n\t\t{}\n\n".format(
                    "\n".join(in1).replace("\n", "\n\t\t").strip("\n\t")
                )

            if in2:
                err_message += "\tItems from nitpycker but not in unittest:\n\t\t{}\n".format(
                    "\n".join(in2).replace("\n", "\n\t\t").strip("\n\t")
                )

            self.fail(err_message)

    @staticmethod
    def extract_headers(output, verbosity):
        """
        Extracts the headers from the output

        :param output: output of the test
        :param verbosity: verbosity used to run the test
        :return: tuple containing the headers and the rest of the output
        """
        if verbosity == 1:
            return output.split("\n", 1)
        elif verbosity == 2:
            return output.split("\n\n", 1)

        return "", output

    def compare_headers(self, unittest_headers, nitpycker_headers, verbosity):
        """
        Compares the headers of the output of unittest and nitpycker

        :param unittest_headers: headers obtained from the unittest test run
        :param nitpycker_headers: headers obtained from the nitpycker test run
        :param verbosity: verbosity used for the test
        """
        if verbosity == 1:
            self.assertCountEqual(unittest_headers, nitpycker_headers)
        elif verbosity == 2:
            self.assertCountEqual(unittest_headers.split("\n"), nitpycker_headers.split("\n"))
        else:
            self.assertEqual(unittest_headers, nitpycker_headers)

    def check_against_unittest(self, test_pattern, verbosity=0, **kwargs):
        """
        Runs both unittest and nitpycker with the given test pattern and
        checks that both output matches

        :param test_pattern: pattern that test must match
        :param verbosity: verbosity with which the test
        :param kwargs: additional arguments to pass to the test runners
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SerializationWarning)
            result1, unittest_output = run_tests(test_pattern, verbosity=verbosity, **kwargs)
            result2, nitpycker_output = run_tests(test_pattern, test_runner=ParallelRunner, verbosity=verbosity, **kwargs)

        regex_time_spent = r'Ran \d+ test(s)? in \d+\.\d+s'
        unittest_time = re.search(regex_time_spent, unittest_output)
        nitpycker_time = re.search(regex_time_spent, nitpycker_output)

        unittest_output = unittest_output[:unittest_time.start()] + unittest_output[unittest_time.end():]
        nitpycker_output = nitpycker_output[:nitpycker_time.start()] + nitpycker_output[nitpycker_time.end():]

        unittest_headers, unittest_output = self.extract_headers(unittest_output, verbosity)
        nitpycker_headers, nitpycker_output = self.extract_headers(nitpycker_output, verbosity)

        self.compare_outputs(set(unittest_output.split("\n\n")), set(nitpycker_output.split("\n\n")))
        self.compare_headers(unittest_headers, nitpycker_headers, verbosity)
        self.assertEqual(result1, result2, "Didn't get the same return codes")

        self.assertEqual(
            unittest_time.group(0).split(" ")[1], nitpycker_time.group(0).split(" ")[1],
            msg="The number of tests ran by unittest and NitPycker is not the same"
        )

        self.assertGreater(int(unittest_time.group(0).split(" ")[1]), 0, msg="No tests where run")


for module in test_modules:  # dynamically add comparisons between nitpycker and unittest
    for args in test_args:
        f_name = get_function_name(module, args)
        set_function(
            UnittestComparisonTest,
            f_name,
            lambda self, test_pattern=module, kwargs=args: self.check_against_unittest(test_pattern, **kwargs)
        )


if __name__ == "__main__":
    unittest.main()
