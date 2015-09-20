#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Managers are use for controlling the plugins invocation. Plugins should never get called by themselves, but rather be
called by a manager in well defined entry points.
"""


import argparse
import importlib
import inspect
import logging
import os
import unittest

from nitpycker.plugins.text_reporter import TextReporter
from nitpycker.plugins import Plugin, TestReporter
from nitpycker.result import ResultAggregator

__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


def get_subclasses(base_class: callable) -> list:
    """
    Gets recursively all non-abstract subclasses of the given base class and returns them as a list

    :param base_class: the base class to inspect
    :return: list of subclasses  for the given base class
    """
    all_subclasses = []
    for subclass in base_class.__subclasses__():
        if not inspect.isabstract(subclass):
            all_subclasses.append(subclass)
        all_subclasses.extend(get_subclasses(subclass))

    return all_subclasses


class Manager:
    """
    The manager is responsible for setup and calling plugins. It has some default entry points and more can be added
    on demand
    """
    all_plugins = []
    enabled_plugins = []

    def __init__(self):
        self.logger = logging.getLogger("nitpycker.plugins.manager")

    def load_plugins(self) -> None:
        """
        Loads all plugins in the nitpycker/plugins directory. Then returns an instance of each one
        """
        for _file_ in os.listdir(os.path.realpath(os.path.dirname(__file__))):
            if _file_.endswith(".py"):
                importlib.import_module("nitpycker.plugins.{}".format(_file_.rstrip(".py")))

        # noinspection PyTypeChecker
        self.all_plugins = [plugin() for plugin in get_subclasses(Plugin) if plugin != TestReporter]

    def add_arguments(self, parser: argparse.ArgumentParser, reporter_parser: argparse.ArgumentParser) -> None:
        """
        Adds the plugins switches to the argument parser

        :param parser: the parser to use to add normal arguments
        :param reporter_parser: the parser to use to add reporters
        """
        for plugin in self.all_plugins:
            plugin.add_arguments(parser=parser, reporter_parser=reporter_parser)

    def enable_plugins(self, plugins: list, arguments: argparse.Namespace) -> int:
        """
        Calls the configuration entry point of all plugins to allow them to setup

        :param plugins: the list of enabled plugins
        :param arguments: additional arguments given to the command line
        :return: 1 on error, else None
        """
        self.enabled_plugins = plugins or []
        if any(plugin.configure(self.enabled_plugins, arguments) for plugin in self.all_plugins):
            self.logger.fatal("At least one plugin was misconfigured. Please check your options")
            return 1

    def pre_test_discovery(self) -> None:
        """
        Runs before the tests are discovered
        """
        for plugin in self.enabled_plugins:
            plugin.pre_test_discovery()

    def post_test_discovery(self) -> None:
        """
        Runs after the tests have been discovered
        """
        for plugin in self.enabled_plugins:
            plugin.post_test_discovery()

    def filter_tests(self, tests: unittest.TestSuite) -> unittest.TestSuite:
        """
        Allows to filter tests to prevent some from running

        :param tests: the testSuite to be run
        """
        filtered_test_suite = tests
        for plugin in self.enabled_plugins:
            filtered_test_suite = plugin.filter_tests(tests) or filtered_test_suite

        return filtered_test_suite

    def pre_test_start(self, test: unittest.TestSuite) -> None:
        """
        Runs all plugins before the start of a test

        :param test: the test that will be run
        """
        for plugin in self.enabled_plugins:
            plugin.pre_test_start(test)

    def post_test_end(self, test: unittest.TestSuite) -> None:
        """
        Runs all plugins after the end of a test

        :param test: the test that will be run
        """
        for plugin in self.enabled_plugins:
            plugin.post_test_end(test)

    def report(self, results: ResultAggregator) -> None:
        """
        allows every plugin to generate a report once all tests have finished

        :param results: the summary of all tests
        """
        reported = False
        for plugin in self.enabled_plugins:
            if hasattr(plugin, "__reporter__"):
                plugin.report(results)
                reported = True

        if not reported:
            TextReporter().report(results)

        for plugin in self.enabled_plugins:
            if not hasattr(plugin, "__reporter__"):
                plugin.report(results)
