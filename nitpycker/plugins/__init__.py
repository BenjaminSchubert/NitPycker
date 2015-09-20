#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Base structures for plugins expanding NitPycker. To be discovered, each plugin has to implement a structure here, or a
subclass of them
"""


from abc import ABCMeta
import argparse
import logging
import unittest

from nitpycker.result import ResultAggregator

__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class Plugin(metaclass=ABCMeta):
    """
    The basic plugin. To create a plugin, it is sufficient to subclass it and override the function(s) needed.
    When enabled by the command line, the plugin will then be called for each defined entry point
    """
    name = None

    def __init__(self):
        self.name = self.name or self.__class__.__name__.lower()
        self.logger = logging.getLogger("nitpycker.plugins.{}".format(self.name))

    def help(self):
        """
        The help message to show beside the command line argument when calling the help message
        :return:
        """
        return self.__class__.__doc__ or "(no help available, sorry)"

    def add_arguments(self, parser: argparse.ArgumentParser, reporter_parser: argparse.ArgumentParser, **kwargs)\
            -> None:
        """
        Adds a command line switch to enable the plugin

        :param parser: the parser to which to add the argument
        :param reporter_parser: the parser to which to add reporters argument, to have them all linked in the same place
        :param kwargs: additional arguments
        """
        self.__add_arguments__(parser)

    def __add_arguments__(self, parser: argparse.ArgumentParser) -> None:
        """
        adds a default "--with-{name}" switch to the argument parser

        :param parser: the parser to sue
        """
        parser.add_argument(
            "--with-{}".format(self.name), action="append_const", const=self, dest="plugins",
            help="Enable plugin {}: {}".format(self.name, self.help())
        )

    def configure(self, enabled_plugins: list, arguments: argparse.Namespace) -> None:
        """
        One time configuration of the plugin before running the tests. Should also be used for arguments validity
        checking, and setup before launching the multiple subprocess

        :param enabled_plugins: the list of enabled plugins
        :param arguments: additional given arguments
        """
        pass

    def pre_test_discovery(self) -> None:
        """ Runs before the test discovery is done """
        pass

    def post_test_discovery(self) -> None:
        """ Runs after all tests have been discovered """
        pass

    def filter_tests(self, tests) -> None:
        """
        Allows for test filtering

        :param tests: the TestSuite that will be run
        """
        pass

    def pre_test_start(self, test: unittest.TestSuite) -> None:
        """
        Runs before each test starts

        :param test: the test to run
        """
        pass

    def post_test_end(self, test: unittest.TestSuite) -> None:
        """
        Runs after each test ends

        :param test: the test that has run
        """
        pass

    def report(self, results: ResultAggregator) -> None:
        """
        Runs after the end of all tests, to generate report files and cleanup

        :param results: the summary of all results
        """
        pass


class TestReporter(Plugin, metaclass=ABCMeta):
    """
    A plugin for reporters, allows adding them to a special namespace in arguments to have them grouped in case they
    don't need any other arguments
    """
    __reporter__ = True

    def add_arguments(self, parser: argparse.ArgumentParser, reporter_parser: argparse.ArgumentParser, **kwargs) \
            -> None:
        """
        Adds te arguments to the reporter_parser instead of the normal parser

        :param parser: the default parser
        :param reporter_parser: the reporter parser
        :param kwargs: additional arguments
        """
        self.__add_arguments__(reporter_parser)
