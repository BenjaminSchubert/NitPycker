#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Argument parsing and base control flow for NitPycker's tests
"""

from argparse import Namespace, ArgumentParser
import multiprocessing
import unittest

from nitpycker.plugins.manager import Manager
from nitpycker.logger import setup_logger
from nitpycker.runners import ParallelRunner


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


logger = None


def parse_args(plugin_manager: Manager) -> Namespace:
    """
    Parses the command line for runtime arguments for nitpycker and returns them

    :param plugin_manager: the plugin manager to add plugin options
    :return: a Namespace instance containing all arguments
    """
    parser = ArgumentParser(prog="nitpycker", description="A test runner base on python's unittest")

    verbosity_parser = parser.add_argument_group("Verbosity")
    verbosity_arguments = verbosity_parser.add_mutually_exclusive_group()
    verbosity_arguments.set_defaults(verbosity=1)
    verbosity_arguments.add_argument("-v", "--verbose", action="store_const", dest="verbosity", const=2)
    verbosity_arguments.add_argument("-q", "--quiet", action="store_const", dest="verbosity", const=0)

    parser.add_argument(
        "-n", "--process", action="store", dest="process_number", default=multiprocessing.cpu_count(), type=int,
        help="The number of process to run. Defaults to the number of cores"
    )

    parser.add_argument(
        "-p", "--pattern", action="store", dest="pattern", default="test*.py", type=str,
        help="Pattern to match tests ('test*.py' default)"
    )

    parser.add_argument(
        "start_directory", default=".",
        help="a list of any number of test modules, classes and test methods."
    )

    reporter_parser = parser.add_argument_group("Result Reporters")

    plugin_manager.add_arguments(parser=parser, reporter_parser=reporter_parser)

    return parser.parse_args()


# noinspection PyUnresolvedReferences
def main() -> bool:
    """
    The main nitpycker runner. Parses the command line and runs the tests

    :return: 0 on success else 1
    """
    global logger
    logger = setup_logger("nitpycker")
    plugin_manager = Manager()
    plugin_manager.load_plugins()
    args = parse_args(plugin_manager)
    if plugin_manager.enable_plugins(args.plugins, args):
        exit(2)

    plugin_manager.pre_test_discovery()
    tests = unittest.defaultTestLoader.discover(args.start_directory, pattern=args.pattern)
    plugin_manager.post_test_discovery()
    tests = plugin_manager.filter_tests(tests)
    report = ParallelRunner(plugin_manager, process_number=args.process_number, verbosity=args.verbosity).run(tests)
    return not report.wasSuccessful()
