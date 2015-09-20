#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Results handler for a multiprocessing setup of unittest.py
"""


from contextlib import suppress
import enum
import queue
import threading
import unittest.result
import unittest.case
import unittest
import time
import sys


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class TestState(enum.Enum):
    """
    Represents all possible results for a test
    """
    success = {"short": ".", "long": "ok"}
    failures = {"short": "F", "long": "FAIL"}
    errors = {"short": "E", "long": "ERROR"}
    skipped = {"short": "s", "long": "skipped"}
    expected_failures = {"short": "x", "long": "expected failure"}
    unexpected_successes = {"short": "u", "long": "UNEXPECTED SUCCESS"}


class TrimmedTest:
    """
    A trimmed down, multiprocessing pickable representation of a TestCase
    """
    def __init__(self, test: unittest.case.TestCase):
        self.__doc__ = test.shortDescription()
        self.__string_representation__ = str(test)
        self.__id__ = test.id()
        # noinspection PyUnresolvedReferences
        self.__time_taken__ = test.time_taken

    # noinspection PyPep8Naming
    def shortDescription(self) -> str:
        """
        Returns the short description for the test.

        :return: the test description
        """
        return self.__doc__

    def __str__(self):
        return self.__string_representation__

    def id(self) -> str:
        """
        get the test id

        :return: the test id, copied from TestCase.id()
        """
        return self.__id__

    @property
    def time_taken(self) -> int:
        """
        Get the time taken for the test to run
        """
        return self.__time_taken__

    def get_test_description(self) -> str:
        """
        The test description. either shortDescription() if defined, or str(self)

        :return: test description
        """
        doc_first_line = self.shortDescription()
        if doc_first_line:
            return '\n'.join((str(self), doc_first_line))
        else:
            return str(self)


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

    def addSuccess(self, test: unittest.case.TestCase) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        """
        test.time_taken = time.time() - self.start_time
        self.result_queue.put((TestState.success.name, TrimmedTest(test)))

    def addFailure(self, test: unittest.case.TestCase, exc_info: tuple) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param exc_info: tuple of the form (Exception class, Exception instance, traceback)
        """
        test.time_taken = time.time() - self.start_time
        self.result_queue.put(
            (TestState.failures.name, TrimmedTest(test), exc_info[:2] + (self._exc_info_to_string(exc_info, test),))
        )

    def addError(self, test: unittest.case.TestCase, exc_info: tuple) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param exc_info: tuple of the form (Exception class, Exception instance, traceback)
        """
        test.time_taken = time.time() - self.start_time
        self.result_queue.put(
            (TestState.errors.name, TrimmedTest(test), exc_info[:2] + (self._exc_info_to_string(exc_info, test),))
        )

    def addExpectedFailure(self, test: unittest.case.TestCase, err: tuple) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param err: tuple of the form (Exception class, Exception instance, traceback)
        """
        test.time_taken = time.time() - self.start_time
        self.result_queue.put((TestState.expected_failures.name, TrimmedTest(test), err[:2] + ("",)))

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        """
        test.time_taken = time.time() - self.start_time
        # noinspection PyProtectedMember
        self.result_queue.put(
            (TestState.unexpected_successes.name, TrimmedTest(test),
             (
                 unittest.case._UnexpectedSuccess,
                 unittest.case._UnexpectedSuccess("This test passed and it shouldn't have"),
                 "This test passed and it shouldn't have")
             )
        )

    def addSkip(self, test: unittest.case.TestCase, reason: str):
        """
        Transforms the test in a pickable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param reason: the reason why the test was skipped
        """
        test.time_taken = time.time() - self.start_time
        self.result_queue.put(
            (TestState.skipped.name, TrimmedTest(test), (unittest.SkipTest, unittest.SkipTest(reason), reason))
        )


class ResultCollector(threading.Thread):
    """
    Results handler. Given a report queue, will reform a complete report from it as what would come from a run
    of unittest.TestResult
    """
    def __init__(self, result_queue: queue.Queue, report_queue: queue.Queue, verbosity: int, number_of_tests: str="?",
                 **kwargs):
        super().__init__(**kwargs)
        self.result_queue = result_queue
        self.report_queue = report_queue
        self.cleanup = False
        self.showAll = verbosity > 1
        self.dots = verbosity == 1
        self.number_of_tests = number_of_tests
        self.template = "({counter:{x}}/{total}): {description:80.80} ... {result}\n"
        self.skip_template = "({counter:{x}}/{total}): {description:80.80}: ... {result} : {reason}\n"

        self.results = {}
        for state in TestState:
            self.results[state.name] = []

    def end_collection(self) -> None:
        """ Tells the thread that is it time to end """
        self.cleanup = True

    def run(self) -> None:
        """
        Iterates over the items in the queue until a SIGTERM is received. On SIGTERM finishes processing and outputs the
        result of it. Then sends the full report on the report_queue
        """
        counter = 0
        while not self.cleanup:
            with suppress(queue.Empty):
                result = self.result_queue.get(timeout=1)
                self.results[result[0]].append(result[1:])
                self.result_queue.task_done()
                counter += 1
                if self.showAll:
                    if TestState[result[0]] == TestState.skipped:
                        template = self.skip_template
                    else:
                        template = self.template
                    sys.stderr.write(template.format(
                        counter=counter,
                        x=len(str(self.number_of_tests)),
                        reason=result[2] if len(result) > 2 else "",
                        total=self.number_of_tests,
                        description=result[1].get_test_description(),
                        result=TestState[result[0]].value["long"]
                    ))
                elif self.dots:
                    sys.stderr.write(TestState[result[0]].value["short"])
                sys.stderr.flush()
        sys.stderr.write("\n")
        sys.stderr.flush()
        self.report_queue.put(self.results)


class ResultAggregator:
    """
    A simple Result class to be returned to the runner for displaying the results
    """
    def __init__(self, results: dict):
        self.results = results

    # noinspection PyPep8Naming
    def wasSuccessful(self) -> bool:
        """
        Returns whether the test was successful or not
        :return: True is the test was successful, else False
        """
        if len(self.results[TestState.errors.name]) == \
                len(self.results[TestState.failures.name]) == \
                len(self.results[TestState.unexpected_successes.name]) == 0:
            return True
        return False

    @property
    def failures(self) -> list:
        """ the list of all test failures """
        return self.results[TestState.failures.name]

    @property
    def errors(self) -> list:
        """ the list of all test errors """
        return self.results[TestState.errors.name]

    @property
    def unexpected_success(self) -> list:
        """ the list of all unexpected success """
        return self.results[TestState.unexpected_successes.name]
