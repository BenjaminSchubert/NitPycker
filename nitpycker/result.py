"""
Results handler for a multiprocessing setup of unittest.py
"""

import enum
import operator
import queue
import threading
import time
import unittest
import unittest.case
import unittest.result

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
        Transforms the test in a serializable version of it and sends it to a queue for further analysis

        :param test: the test to save
        """
        # noinspection PyTypeChecker
        self.add_result(TestState.success, test)

    def addFailure(self, test: unittest.case.TestCase, exc_info: tuple) -> None:
        """
        Transforms the test in a serializable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param exc_info: tuple of the form (Exception class, Exception instance, traceback)
        """
        # noinspection PyTypeChecker
        self.add_result(TestState.failure, test, exc_info)

    def addError(self, test: unittest.case.TestCase, exc_info: tuple) -> None:
        """
        Transforms the test in a serializable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param exc_info: tuple of the form (Exception class, Exception instance, traceback)
        """
        # noinspection PyTypeChecker
        self.add_result(TestState.error, test, exc_info)

    def addExpectedFailure(self, test: unittest.case.TestCase, err: tuple) -> None:
        """
        Transforms the test in a serializable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param err: tuple of the form (Exception class, Exception instance, traceback)
        """
        # noinspection PyTypeChecker
        self.add_result(TestState.expected_failure, test, err)

    def addUnexpectedSuccess(self, test: unittest.case.TestCase) -> None:
        """
        Transforms the test in a serializable version of it and sends it to a queue for further analysis

        :param test: the test to save
        """
        # noinspection PyTypeChecker
        self.add_result(TestState.unexpected_success, test)

    def addSkip(self, test: unittest.case.TestCase, reason: str):
        """
        Transforms the test in a serializable version of it and sends it to a queue for further analysis

        :param test: the test to save
        :param reason: the reason why the test was skipped
        """
        test.time_taken = time.time() - self.start_time
        test._outcome = None
        self.result_queue.put((TestState.skipped, test, reason))


class ResultCollector(threading.Thread, unittest.result.TestResult):
    """
    Results handler. Given a report queue, will reform a complete report from it as what would come from a run
    of unittest.TestResult

    :param stream: stream on which to write information
    :param descriptions: whether to display tests descriptions or not
    :param verbosity: the verbosity used for the test result reporters
    :param result_queue: queue form which to get the test results
    :param test_results: list of testResults instances to use
    """
    def __init__(self, stream=None, descriptions=None, verbosity=None, *, result_queue: queue.Queue, test_results):
        threading.Thread.__init__(self)
        unittest.result.TestResult.__init__(self, stream, descriptions, verbosity)
        self.test_results = test_results

        for testResult in self.test_results:
            if hasattr(testResult, "separator1"):
                self.separator1 = testResult.separator1
                break

        for testResult in self.test_results:
            if hasattr(testResult, "separator2"):
                self.separator2 = testResult.separator2
                break

        self.result_queue = result_queue
        self.cleanup = False
        self.showAll = verbosity > 1
        self.dots = verbosity == 1

        self.stream = stream
        self.descriptions = descriptions

        self.results = {}
        for state in TestState:
            self.results[state.name] = []

    def end_collection(self) -> None:
        """ Tells the thread that is it time to end """
        self.cleanup = True

    def _call_test_results(self, method_name, *args, **kwargs):
        """
        calls the given method on every test results instances

        :param method_name: name of the method to call
        :param args: arguments to pass to the method
        :param kwargs: keyword arguments to pass to the method
        """
        method = operator.methodcaller(method_name, *args, **kwargs)
        for testResult in self.test_results:
            method(testResult)

    # noinspection PyPep8Naming
    def getDescription(self, test):
        """
        Get the description of the test

        :param test: test from which to get the description
        :return: description of the test
        """
        doc_first_line = test.shortDescription()
        if self.descriptions and doc_first_line:
            return '\n'.join((str(test), doc_first_line))
        else:
            return str(test)

    def test_info(self, test):
        """
        writes test description on the stream used for reporting

        :param test: test for which to display information
        """
        if self.showAll:
            self.stream.write(self.getDescription(test))
            self.stream.write(" ... ")
            self.stream.flush()

    def addError(self, test, err):
        """
        registers a test as error

        :param test: test to register
        :param err: error the test gave
        """
        super().addError(test, err)
        self.test_info(test)
        self._call_test_results('addError', test, err)

    def addExpectedFailure(self, test, err):
        """
        registers as test as expected failure

        :param test: test to register
        :param err: error the test gave
        """
        super().addExpectedFailure(test, err)
        self.test_info(test)
        self._call_test_results('addExpectedFailure', test, err)

    def addFailure(self, test, err):
        """
        registers a test as failure

        :param test: test to register
        :param err: error the test gave
        """
        super().addFailure(test, err)
        self.test_info(test)
        self._call_test_results('addFailure', test, err)

    def addSkip(self, test, reason):
        """
        registers a test as skipped

        :param test: test to register
        :param reason: reason why the test was skipped
        """
        super().addSkip(test, reason)
        self.test_info(test)
        self._call_test_results('addSkip', test, reason)

    def addSuccess(self, test):
        """
        registers a test as successful

        :param test: test to register
        """
        super().addSuccess(test)
        self.test_info(test)
        self._call_test_results('addSuccess', test)

    def addUnexpectedSuccess(self, test):
        """
        registers a test as an unexpected success

        :param test: test to register
        """
        super().addUnexpectedSuccess(test)
        self.test_info(test)
        self._call_test_results('addUnexpectedSuccess', test)

    def printErrors(self):
        """
        print test report
        """
        self._call_test_results('printErrors')

    def run(self) -> None:
        """
        processes entries in the queue until told to stop
        """
        while not self.cleanup:
            try:
                result, test, additional_info = self.result_queue.get(timeout=1)
            except queue.Empty:
                continue

            self.testsRun += 1
            self.result_queue.task_done()

            if result == TestState.success:
                self.addSuccess(test)
            else:
                if result == TestState.failure:
                    self.addFailure(test, additional_info)
                elif result == TestState.error:
                    self.addError(test, additional_info)
                elif result == TestState.skipped:
                    self.addSkip(test, additional_info)
                elif result == TestState.expected_failure:
                    self.addExpectedFailure(test, additional_info)
                elif result == TestState.unexpected_success:
                    self.addUnexpectedSuccess(test)
                else:
                    raise Exception("This is not a valid test type :", result)
