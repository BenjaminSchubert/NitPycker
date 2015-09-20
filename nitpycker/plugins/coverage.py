#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Plugin for NitPycker implementing coverage for the code
"""


import argparse
import functools
import multiprocessing
import multiprocessing.util
import unittest

try:
    import coverage
    import coverage.collector
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False

from nitpycker.plugins import Plugin


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class Coverage(Plugin):
    """
    coverage reporting of your tests
    """
    cover_xml = None
    cover_html = None
    cover_inclusive = None
    coverage_instance = None
    cover_output_stdout = None
    cover_branch = None

    def add_arguments(self, parser: argparse.ArgumentParser, **kwargs) -> None:
        """
        Adds the different arguments to the command line

        :param parser: the argument parser to which to add the arguments
        :param kwargs: additional arguments
        """
        group = parser.add_argument_group("Coverage")
        super().add_arguments(group, **kwargs)
        group.add_argument("--cover-xml", action="store_true", dest="cover_xml", help="generates a xml report")
        group.add_argument("--cover-html", action="store_true", dest="cover_html", help="generates an html report")
        group.add_argument(
            "--cover-inclusive", action="store_true", dest="cover_inclusive",
            help="Includes all python files under the working directory in the report. "
            "Useful for discovering untested files or dead code"
        )
        group.add_argument(
            "--cover-no-stdout", action="store_false", dest="cover_output_stdout",
            help="Don't output coverage report on stdout"
        )
        group.add_argument(
            "--cover-branch", action="store_true", dest="cover_branch",
            help="Cover branches too"
        )

    # noinspection PyUnresolvedReferences
    def configure(self, enabled_plugins: list, arguments: argparse.Namespace) -> int:
        """
        Checks that no cover arguments has been given if coverage was not enabled and saves the arguments for later use

        :param enabled_plugins: the list of enabled plugins
        :param arguments: all the other arguments given on the command line
        :return: 1 on error, None else
        """
        if self not in enabled_plugins and \
                (arguments.cover_xml or arguments.cover_html or arguments.cover_inclusive or arguments.cover_branch or
                 not arguments.cover_output_stdout):
            self.logger.error("Coverage was not enabled explicitly, but arguments concerning it were enabled.")
            self.logger.error("If you really want coverage, please enable it explicitly.")
            return 1

        self.cover_xml = arguments.cover_xml
        self.cover_html = arguments.cover_html
        self.cover_inclusive = arguments.cover_inclusive
        self.cover_output_stdout = arguments.cover_output_stdout
        self.cover_branch = arguments.cover_branch

    def pre_test_discovery(self) -> None:
        """ Starts coverage for the tests """
        self.coverage_instance = coverage.coverage(
            data_suffix="discovery", branch=self.cover_branch, auto_data=False, source="."
        )
        self.coverage_instance.start()

    def post_test_discovery(self) -> None:
        """ Stops coverage for the tests """
        self.coverage_instance.stop()
        self.coverage_instance.save()

    def pre_test_start(self, test: unittest.TestSuite) -> None:
        """
        starts coverage logging in a new file

        :param test: the test to cover
        """
        last_method = str(test).split("<")[-1].split(">")[0]
        module = last_method.split(" ")[0].lower()
        method_name = last_method.split("=")[-1]
        suffix = ".".join([module, method_name])
        self.coverage_instance = coverage.coverage(
            data_suffix=suffix, branch=self.cover_branch, auto_data=False, source="."
        )
        self.coverage_instance.start()
        self.__setup_multiprocess_coverage__()

    def post_test_end(self, test: unittest.TestSuite) -> None:
        """
        Saves the coverage for the given test

        :param test: the test to cover
        """
        self.coverage_instance.stop()
        self.coverage_instance.save()

    def report(self, *args) -> None:
        """
        Generates the full coverage report once the tests have run

        :param args: additional arguments
        """
        self.coverage_instance = coverage.coverage(
            data_suffix="combined", branch=self.cover_branch, auto_data=False, source="."
        )
        self.coverage_instance.combine()
        self.coverage_instance.save()

        if self.cover_output_stdout:
            self.coverage_instance.report()

        if self.cover_xml:
            self.coverage_instance.xml_report()

        if self.cover_html:
            self.coverage_instance.html_report()

    def __setup_multiprocess_coverage__(self) -> None:
        """
        Patches the multiprocessing.Process instance to start running new coverage instance when launched
        """
        def terminate_process(cov: coverage.coverage) -> None:
            """
            Once the process is finished, stop and save coverage

            :param cov: the coverage instance
            """
            cov.stop()
            cov.save()

        def setup_process(_: object, cover_branch: bool) -> None:
            """
            launches coverage for the process and registers the terminate

            :param _: callable, unused
            :param cover_branch: whether to cover branches or not
            """
            cov = coverage.coverage(data_suffix=True, branch=cover_branch, auto_data=False, source=".")
            cov.start()
            multiprocessing.util.Finalize(None, terminate_process, args=(cov,), exitpriority=1000)

        part = functools.partial(setup_process, self.cover_branch)
        multiprocessing.util.register_after_fork(part, part)


if not COVERAGE_AVAILABLE:
    # we unset Coverage if it's not available
    Coverage = None
