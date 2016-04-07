#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Results handler for a multiprocessing setup of unittest.py
"""

import enum
import queue
import sys
import threading
import time
import unittest
import unittest.case
import unittest.result
from contextlib import suppress

# noinspection PyProtectedMember
from unittest.runner import _WritelnDecorator

import collections

from nitpycker.excinfo import FrozenExcInfo


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class TestState(enum.Enum):
    """
    Represents all possible results for a test
    """
    success = "success"
    failure = "failures"
    error = "errors"
    skipped = "skipped"
    expected_failure = "expected failures"
    unexpected_success = "unexpected successes"


class InterProcessResult(unittest.result.TestResult):
    """
    A TestResult implementation to put results in a queue, for another thread to consume
    """
    def __init__(self, result_queue: queue.Queue):
        super().__init__()
        self.result_queue = result_queue
        self.start_time = self.stop_time = None

    def startTest(self, test: unittest.case.TestCase) -> None:
        """
        Saves the time before starting the test

        :param test: the test that is going to be run
        """
        self.start_time = time.time()

    def add_result(self, _type, test, exc_info=None):
        """
        Adds the given result to the list

        :param _type: type of the state of the test (TestState.failure, TestState.error, ...)
        :param test: the test
        :param exc_info: additional execution information
        """
        if exc_info is not None:
            exc_info = FrozenExcInfo(exc_info)
        test.time_taken = time.time() - self.start_time
        test._outcome = None
        self.result_queue.put((_type, test, exc_info))

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        """
        self.add_result(TestState.success, test)

    def addFailure(self, test: unittest.case.TestCase, exc_info: tuple) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param exc_info: tuple of the form (Exception class, Exception instance, traceback)
        """
        self.add_result(TestState.failure, test, exc_info)

    def addError(self, test: unittest.case.TestCase, exc_info: tuple) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param exc_info: tuple of the form (Exception class, Exception instance, traceback)
        """
        self.add_result(TestState.error, test, exc_info)

    def addExpectedFailure(self, test: unittest.case.TestCase, err: tuple) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param err: tuple of the form (Exception class, Exception instance, traceback)
        """
        self.add_result(TestState.expected_failure, test, err)

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        """
        self.add_result(TestState.unexpected_success, test)

    def addSkip(self, test: unittest.case.TestCase, reason: str):
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param reason: the reason why the test was skipped
        """
        test.time_taken = time.time() - self.start_time
        test._outcome = None
        self.result_queue.put((TestState.skipped, test, reason))


class ResultCollector(threading.Thread):
    """
    Results handler. Given a report queue, will reform a complete report from it as what would come from a run
    of unittest.TestResult
    """
    def __init__(self, result_queue: queue.Queue, verbosity: int, number_of_tests: str="?",
                 **kwargs):
        super().__init__(**kwargs)
        self.CHANGEME = unittest.TextTestResult(_WritelnDecorator(sys.stderr), True, 1)
        self.result_queue = result_queue
        self.cleanup = False
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.number_of_tests = number_of_tests
        self.__exit_code = None

        self.results = {}
        for state in TestState:
            self.results[state.name] = []

    def end_collection(self) -> None:
        """ Tells the thread that is it time to end """
        print("CALLED GOODBYE")
        self.cleanup = True

    @property
    def exitcode(self):
        if self.__exit_code is None:
            raise Exception("Couldn't get the thread exit code")
        return self.__exit_code

    def print_summary(self, counters, success_counter, time_taken):
        errors = sum(counters.values())

        sys.stderr.write("-" * 70 + "\n")
        sys.stderr.write("Ran {number_of_tests} test{s} in {time:.2f}s\n\n".format(
            number_of_tests=errors + success_counter, s="s" if errors > 1 else "", time=time_taken),
        )

        info = []
        for state in TestState:
            if counters[state]:
                info.append("{description}={number}".format(
                    description=state.value, number=counters[state])
                )

        if len(info) != 0:
            sys.stderr.write("FAILED " + "({})".format(", ".join(info)) + "\n")
        else:
            sys.stderr.write("OK\n")

    def run(self) -> None:
        """
        Iterates over the items in the queue until a SIGTERM is received. On SIGTERM finishes processing and outputs the
        result of it. Then sends the full report on the report_queue
        """
        counters = collections.Counter()
        success_counter = 0
        start_time = time.time()

        while not self.cleanup:
            with suppress(queue.Empty):
                result, test, additional_info = self.result_queue.get(timeout=1)

                if result == TestState.success:
                    self.CHANGEME.addSuccess(test)
                    success_counter += 1
                else:
                    counters.update((result,))
                    if result == TestState.failure:
                        self.CHANGEME.addFailure(test, additional_info)
                    elif result == TestState.error:
                        self.CHANGEME.addError(test, additional_info)
                    elif result == TestState.skipped:
                        self.CHANGEME.addSkip(test, additional_info)
                    elif result == TestState.expected_failure:
                        self.CHANGEME.addExpectedFailure(test, additional_info)
                    elif result == TestState.unexpected_success:
                        self.CHANGEME.addUnexpectedSuccess(test)
                    else:
                        raise Exception("This is not a valid test type :", result)
                self.result_queue.task_done()

        time_taken = time.time() - start_time

        self.CHANGEME.printErrors()
        self.print_summary(counters, success_counter, time_taken)
        self.__exit_code = any(counters.values())
