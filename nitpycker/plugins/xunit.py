#!/usr/bin/python3
# -*- coding: UTF-8 -*-


"""
Xunit compliant XML reporter
"""


import os
from xml.etree import ElementTree

from nitpycker.plugins import TestReporter
from nitpycker.result import TestState, ResultAggregator

__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class XMLReporter(TestReporter):
    """
    An Xunit compliant reporter, useful mainly for CI integration
    """
    @staticmethod
    def add_error_list(report: ElementTree.Element, results: dict) -> None:
        """
        Adds every result to the XML document tree

        :param report: the XML document tree to use
        :param results: contains lists of tests to add
        """
        for tests in results:
            for test in results[tests]:
                testcase = ElementTree.Element(
                    'testcase',
                    attrib={
                        "classname": ".".join(test[0].id().split(".")[:-1]),
                        "name": test[0].id().split(".")[-1],
                        "time": str(round(test[0].time_taken, 3))
                    }
                )

                if tests == TestState.unexpected_successes.name:
                    _type_ = TestState.failures.name
                elif tests == TestState.expected_failures.name:
                    _type_ = None
                else:
                    _type_ = tests

                if len(test) > 1:
                    fail_type = ElementTree.Element(
                        _type_,
                        attrib={
                            "type": test[1][0].__name__,
                            "message": str(test[1][1])
                        }
                    )
                    fail_type.text = test[1][2]

                    # TODO add stdout and stderr capture here
                    testcase.append(fail_type)
                report.append(testcase)

    def report(self, result_reporter: ResultAggregator) -> None:
        """
        creates an xml rapport for the test. This is xunit compliant

        :param result_reporter: results to parse
        """
        report = ElementTree.Element(
            "testsuite",
            attrib={
                "name": os.path.basename(os.getcwd()),
                "tests": str(sum(len(test_type) for test_type in result_reporter.results.values())),
                "errors": str(len(result_reporter.results[TestState.errors.name])),
                "failures": str(sum(
                    len(result_reporter.results[test_type])
                    for test_type in [TestState.failures.name, TestState.unexpected_successes.name])),
                "skip": str(len(result_reporter.results[TestState.skipped.name]))
            }
        )
        if sum(len(test_type) for test_type in result_reporter.results.values()):
            self.add_error_list(report, result_reporter.results)

        with open("nitpycker.xml", "wb") as f:
            ElementTree.ElementTree(report).write(f, encoding="utf-8", xml_declaration=True)
