#!/usr/bin/env python3

"""
Tests to check that the output of NitPycker is the same as the one
of unittest in cases where no multiprocessing is involved
"""


import unittest

import os
import re
import collections

from nitpycker.runner import ParallelRunner
from nitpycker.test import run_tests


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


test_modules = [
    "check_tests_incomes.py",
    "check_module_import_failure.py",
    "check_class_no_parallel.py",
    "check_module_no_parallel.py"
]


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

        if any([in1, in2]):
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

    def check_against_unittest(self, test_pattern, **kwargs):
        """
        Runs both unittest and nitpycker with the given test pattern and
        checks that both output matches

        :param test_pattern: pattern that test must match
        :param kwargs: additional arguments to pass to the test runners
        """
        result1, unittest_output = run_tests(test_pattern, **kwargs)
        result2, nitpycker_output = run_tests(test_pattern, test_runner=ParallelRunner, **kwargs)

        regex_time_spent = r'Ran \d+ test(s)? in \d+\.\d+s'
        unittest_time = re.search(regex_time_spent, unittest_output)
        nitpycker_time = re.search(regex_time_spent, nitpycker_output)

        self.assertEqual(
            unittest_time.group(0).split(" ")[1], nitpycker_time.group(0).split(" ")[1],
            msg="The number of tests ran by unittest and NitPycker is not the same"
        )

        unittest_output = unittest_output[:unittest_time.start()] + unittest_output[unittest_time.end():]
        nitpycker_output = nitpycker_output[:nitpycker_time.start()] + nitpycker_output[nitpycker_time.end():]

        unittest_results, unittest_output = unittest_output.split("\n", 1)
        nitpycker_results, nitpycker_output = nitpycker_output.split("\n", 1)

        self.compare_outputs(set(unittest_output.split("\n\n")), set(nitpycker_output.split("\n\n")))
        self.assertEqual(collections.Counter(unittest_results), collections.Counter(nitpycker_results))
        self.assertEqual(result1, result2, "Didn't get the same return codes")


for module in test_modules:
    for args in [{}, {"verbosity": 1}]:
        f_name = "test_{}{}".format(
            os.path.splitext(module)[0].replace("check_", ""),
            "_" + "_".join(["{}_{}".format(key, value) for key, value in args.items()] if len(args) else "")
        ).strip("_")

        setattr(
            UnittestComparisonTest,
            f_name,
            lambda self, test_pattern=module, kwargs=args: self.check_against_unittest(test_pattern, **kwargs)
        )
        setattr(getattr(UnittestComparisonTest, f_name), "__name__", f_name)


if __name__ == "__main__":
    unittest.main()
