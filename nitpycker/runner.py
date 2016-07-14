"""
This modules implements a Parallel test runner for unittest
"""


import collections
from multiprocessing import Process, cpu_count
from multiprocessing.pool import Pool, MaybeEncodingError
import sys
import time
import unittest
# noinspection PyProtectedMember
from unittest.runner import _WritelnDecorator, TextTestResult
import warnings

from nitpycker.result import InterProcessResult, ResultCollector


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class TestClassNotIterable(Exception):
    """
    Exception thrown when a testClass, that should be iterable
    is not. This is likely to be because the module couldn't be
    imported correctly, and will likely not be serializable, so
    we should run it locally
    """


class SerializationWarning(UserWarning):
    """
    Warning to be raised when a solvable problem appeared while serializing an object
    """


class NonDaemonizeableProcess(Process):
    """
    Process that cannot be set as a daemon
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def daemon(self):
        """ whether the process is a daemon or not, this is always false """
        return False

    @daemon.setter
    def daemon(self, daemonic):
        pass


class NitPyckerPool(Pool):
    """
    Process pool that uses a non daemonizable process for its job
    """
    Process = NonDaemonizeableProcess

    def __reduce__(self):
        raise NotImplementedError('pool objects cannot be passed between processes or pickled')


def run_test(args):
    """
    runs the test given as argument

    :param args: tuple containing an id for the test and the test to run
    :return: index, results of the tests
    """
    index, test = args

    result = InterProcessResult()
    test.run(result)
    return index, result.get_results()


class ParallelRunner:
    """
    A parallel test runner for unittest

    :param stream: stream to use for tests reporting
    :param descriptions: whether to display descriptions or not
    :param verbosity: verbosity of the test result reporters
    :param failfast: stops the test on the first error or failure
    :param buffer: whether to buffer output of the test or not. On buffering, this
            will discard output for passing tests and display normally on failing tests
    :param resultclass: single or list of result class to use
    :param warnings: warning filter that should be used while running the tests
    :param tb_locals: if true, local variables will be shown in tracebacks
    :param process_number: number of processes to use for running the tests
    """
    # TODO implement buffering
    # TODO implement failfast
    # TODO implement warnings
    # TODO verify tb_locals works
    resultclass = (TextTestResult,)
    result_collector_class = ResultCollector

    def __init__(self, stream=None, descriptions=True, verbosity=1, failfast=False, buffer=False, resultclass=None,
                 warnings=None, *, tb_locals=False, process_number=cpu_count(),
                 result_collector_class=None):
        if stream is None:
            stream = sys.stderr
        self.stream = _WritelnDecorator(stream)
        self.descriptions = descriptions
        self.verbosity = verbosity
        self.failfast = failfast
        self.buffer = buffer
        self.tb_locals = tb_locals
        self.warnings = warnings

        self.process_number = process_number

        if resultclass is not None:
            if isinstance(resultclass, collections.Iterable):
                self.resultclass = resultclass
            else:
                self.resultclass = (resultclass,)

        if result_collector_class is not None:
            self.result_collector_class = result_collector_class

    # noinspection PyPep8Naming
    def _makeResult(self):
        """ instantiates the result class reporters """
        return [reporter(self.stream, self.descriptions, self.verbosity) for reporter in self.resultclass]

    @staticmethod
    def module_can_run_parallel(test_module: unittest.TestSuite) -> bool:
        """
        Checks if a given module of tests can be run in parallel or not

        :param test_module: the module to run
        :return: True if the module can be run on parallel, False otherwise
        """
        for test_class in test_module:
            # if the test is already failed, we just don't filter it
            # and let the test runner deal with it later.
            if hasattr(unittest.loader, '_FailedTest'):  # import failure in python 3.4.5+
                # noinspection PyProtectedMember
                if isinstance(test_class, unittest.loader._FailedTest):
                    continue

            if not isinstance(test_class, collections.Iterable):  # likely an import failure in python 3.4.4-
                # before python 3.4.5, test import failures were not serializable.
                # We are unable to be sure that this is a module import failure, but it very likely is
                # if this is the case, we'll just run this locally and see
                raise TestClassNotIterable()

            for test_case in test_class:
                return not getattr(sys.modules[test_case.__module__], "__no_parallel__", False)

    @staticmethod
    def class_can_run_parallel(test_class: unittest.TestSuite) -> bool:
        """
        Checks if a given class of tests can be run in parallel or not

        :param test_class: the class to run
        :return: True if te class can be run in parallel, False otherwise
        """
        for test_case in test_class:
            return not getattr(test_case, "__no_parallel__", False)

        # this only happens when there are no tests in the class
        return True

    def collect_tests(self, tests):
        """
        split all tests into chunks to be executed on multiple processes

        :param tests: tests that need to be run
        :return: list of tests suites, test that need to be run locally
        """

        test_suites = []
        local_test_suites = unittest.TestSuite()

        for test_module in tests:
            try:
                can_run_parallel = self.module_can_run_parallel(test_module)
            except TestClassNotIterable:
                local_test_suites.addTest(test_module)
                continue
            else:
                if not can_run_parallel:
                    test_suites.append(test_module)
                    continue

            for test_class in test_module:
                if not self.class_can_run_parallel(test_class):
                    test_suites.append(test_class)
                    continue

                for _test in test_class:
                    test_suite = unittest.TestSuite()
                    test_suite.addTest(_test)
                    test_suites.append(test_suite)

        return test_suites, local_test_suites

    def print_summary(self, result, time_taken):
        """
        Prints the test summary, how many tests failed, how long it took, etc

        :param result: result class to use to print summary
        :param time_taken: the time all tests took to run
        """
        if hasattr(result, "separator2"):
            self.stream.writeln(result.separator2)

        self.stream.writeln("Ran {number_of_tests} test{s} in {time:.3f}s\n".format(
            number_of_tests=result.testsRun, s="s" if result.testsRun != 1 else "", time=time_taken
        ))

        info = []
        if not result.wasSuccessful():
            self.stream.write("FAILED")

            if result.failures:
                info.append("failures={}".format(len(result.failures)))
            if result.errors:
                info.append("errors={}".format(len(result.errors)))
        else:
            self.stream.write("OK")

        if result.skipped:
            info.append("skipped={}".format(len(result.skipped)))
        if result.expectedFailures:
            info.append("expected failures={}".format(len(result.expectedFailures)))
        if result.unexpectedSuccesses:
            info.append("unexpected successes={}".format(len(result.unexpectedSuccesses)))

        if info:
            self.stream.writeln(" ({})".format(", ".join(info)))
        else:
            self.stream.write("\n")

    def run(self, test: unittest.TestSuite):
        """
        Given a TestSuite, will create one process per test case whenever possible and run them concurrently.
        Will then wait for the result and return them

        :param test: the TestSuite to run
        :return: a summary of the test run
        """
        start_time = time.time()
        test_suites, local_test_suites = self.collect_tests(test)

        results_collector = ResultCollector(
            self.stream, self.descriptions, self.verbosity,
            test_results=self._makeResult(),
        )

        with NitPyckerPool(self.process_number) as pool:
            results = pool.imap_unordered(
                run_test,
                [(index, suite) for index, suite in enumerate(test_suites)]
            )

            local_test_suites.run(results_collector)

            while True:
                try:
                    _, result_list = next(results)
                except StopIteration:
                    break
                except MaybeEncodingError as e:
                    index = int(e.value.lstrip("(").split(",")[0])
                    test = test_suites[index]
                    warnings.warn("Serialization error: {} on test {}".format(
                        e.exc, test), SerializationWarning)
                    test.run(results_collector)
                else:
                    for result in result_list:
                        state, test, additional_info = result
                        results_collector.register(state, test, additional_info)

        results_collector.printErrors()
        self.print_summary(results_collector, time.time() - start_time)

        return results_collector
