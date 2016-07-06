#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
This modules implements a Parallel test runner for unittest
"""

import multiprocessing
import queue
import sys
import threading
import unittest

from nitpycker.result import InterProcessResult, ResultCollector

__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class ParallelRunner:
    """
    A parallel test runner for unittest

    :param process_number: the number of process to launch to run the tests
    :param verbosity: Processes verbosity
    """
    class Process(multiprocessing.Process):
        """
        A simple test runner for a TestSuite.

        :param test: the unittest.TestSuite to rnu
        :param results_queue: a queue where to put the results once done
        :param manager: the plugin manager to be called before and after the run
        :param task_done_notifier: semaphore to acquire to notify from end of task
        """
        def __init__(self, test: unittest.TestSuite, results_queue: queue.Queue,
                     task_done_notifier: threading.Semaphore, **kwargs):
            super().__init__(**kwargs)
            self.test = test
            self.results = InterProcessResult(results_queue)
            self.task_done = task_done_notifier

        def run(self) -> None:
            """ Launches the test and notifies of the result """
            try:
                self.test(self.results)
            finally:
                self.task_done.release()

    def __init__(self, stream=None, descriptions=True, verbosity=1, failfast=False, buffer=False, resultclass=None,
                 warnings=None, process_number=multiprocessing.cpu_count()):
        self.verbosity = verbosity
        self.process_number = process_number

    @staticmethod
    def module_can_run_parallel(test_module: unittest.TestSuite) -> bool:
        """
        Checks if a given module of tests can be run in parallel or not

        :param test_module: the module to run
        :return: True if the module can be run on parallel, False otherwise
        """
        for test_class in test_module:
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

    def run(self, test: unittest.TestSuite):
        """
        Given a TestSuite, will create one process per test case whenever possible and run them concurrently.
        Will then wait for the result and return them

        :param test: the TestSuite to run
        :return: a summary of the test run
        """
        process = []
        resource_manager = multiprocessing.Manager()
        results_queue = resource_manager.Queue()
        tasks_running = resource_manager.BoundedSemaphore(self.process_number)

        test_suites = []
        number_of_tests = 0
        for test_module in test:
            if not self.module_can_run_parallel(test_module):
                number_of_tests += test_module.countTestCases()
                test_suites.append(test_module)
                continue

            for test_class in test_module:
                if not self.class_can_run_parallel(test_class):
                    number_of_tests += test_class.countTestCases()
                    test_suites.append(test_class)
                    continue

                for _test in test_class:
                    number_of_tests += 1
                    test_suite = unittest.TestSuite()
                    test_suite.addTest(_test)
                    test_suites.append(test_suite)

        results_collector = ResultCollector(
            results_queue, self.verbosity, daemon=True)
        results_collector.start()

        for suite in test_suites:
            tasks_running.acquire()
            x = self.Process(suite, results_queue, tasks_running)
            x.start()
            process.append(x)

        for i in process:
            i.join()

        results_queue.join()
        results_collector.end_collection()
        results_collector.join()

        return results_collector