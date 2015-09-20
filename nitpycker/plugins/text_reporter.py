#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
A simple stdout reporter for the tests
"""

import sys

from nitpycker.plugins import TestReporter
from nitpycker.result import TestState, ResultAggregator, TrimmedTest


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


def err_print(string: str, **kwargs) -> None:
    """
    Prints the given message to stderr

    :param string: the string to print
    :param kwargs: additional arguments to pass to the print function
    """
    print(string, file=sys.stderr, **kwargs)


class TextReporter(TestReporter):
    """
    Simple Stdout reporter for tests
    """
    separator_1 = "=" * 70
    separator_2 = "-" * 70

    # noinspection PyPep8Naming
    @staticmethod
    def getDescription(test: TrimmedTest) -> str:
        """
        returns the description of the test

        :param test: the test from which to get the description
        :return: the description
        """
        doc_first_line = test.shortDescription()
        if doc_first_line:
            return '\n'.join((str(test), doc_first_line))
        else:
            return str(test)

    def report(self, report: ResultAggregator) -> int:
        """
        Prints all tests that failed or add errors on stdout

        :param report: the report for all tests
        :return: 1 on success
        """
        self.printErrorList(TestState.errors.value["long"], report.errors)
        self.printErrorList(TestState.failures.value["long"], report.failures)
        self.printErrorList(TestState.unexpected_successes.value["long"], report.unexpected_success)
        err_print(self.separator_2)
        return 1

    # noinspection PyPep8Naming
    def printErrorList(self, flavour: str, errors: list) -> None:
        """
        Prints test description for each tests in the given errors list.

        :param flavour: the type of the failed tests, for display
        :param errors: the list of tests to display
        """
        for test, err in errors:
            err_print(self.separator_1)
            err_print("{flavour}: {description}".format(flavour=flavour, description=self.getDescription(test)))
            err_print(self.separator_2)
            err_print(err[2])
