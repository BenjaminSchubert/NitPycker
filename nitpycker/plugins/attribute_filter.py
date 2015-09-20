#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
A plugin to filter tests corresponding to a given attribute only
"""

import argparse
import unittest

from nitpycker.plugins import Plugin


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class AttributeFilter(Plugin):
    """
    A plugin implementing test filtering for given attributes
    """
    filters = None

    def add_arguments(self, parser: argparse.ArgumentParser, reporter_parser: argparse.ArgumentParser, **kwargs) \
            -> None:
        """
        Allows to add a filter on tests to run based on attributes

        :param parser: the parser on which to add the filter
        :param reporter_parser: not used
        :param kwargs: not used
        """
        parser.add_argument(
            "-a", "--attr", action='append', dest='attribute_filters',
            help="Run only tests having the specified attributes evaluating to 'True'"
        )

    # noinspection PyUnresolvedReferences
    def configure(self, enabled_plugins: list, arguments: argparse.Namespace) -> None:
        """
        Adds itself to the list of enabled plugins and saves the filters

        :param enabled_plugins: list of enabled plugins
        :param arguments: arguments from the command line
        """
        if arguments.attribute_filters is not None:
            enabled_plugins.append(self)
            self.filters = arguments.attribute_filters

    def filter_tests(self, tests: unittest.TestSuite) -> unittest.TestSuite:
        """
        Iterates over tests and removes the one that do not have on of the given attributes

        :param tests: tests scheduled to run
        :return: tests that will be run
        """
        tests_to_be_run = unittest.TestSuite()
        for test in tests:
            added = False
            for _filter_ in self.filters:
                if getattr(test, _filter_, False):
                    tests_to_be_run.addTest(test)
                    added = True

                elif isinstance(test, unittest.TestCase):
                    # noinspection PyProtectedMember
                    if getattr(getattr(test.__class__, test._testMethodName), "unittest", False):
                        tests_to_be_run.addTest(test)
                        added = True

            if not added and isinstance(test, unittest.TestSuite):
                new_test_suite = self.filter_tests(test)
                if new_test_suite.countTestCases() > 0:
                    tests_to_be_run.addTest(new_test_suite)

        return tests_to_be_run
