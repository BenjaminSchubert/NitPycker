#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sample tests, not all functioning to compare against unittest output in order to have the same output (enhanced)
"""

import unittest


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class MyTestCase(unittest.TestCase):
    def test_failure(self):
        self.assertEqual(True, False)

    def test_success(self):
        self.assertEqual(True, True)

    # noinspection PyMethodMayBeStatic
    def test_error(self):
        raise Exception()

    @unittest.expectedFailure
    def test_expected_failure(self):
        self.assertTrue(False)

    @unittest.expectedFailure
    def test_unexpected_success(self):
        self.assertTrue(True)

    @unittest.skip("This has to be skipped")
    def test_skip(self):
        """ This is empty """


class SetupClassTest(unittest.TestCase):
    """ Tests that the setupClass works correctly """
    @classmethod
    def setUpClass(cls):
        cls.value = True

    def test_value(self):
        self.assertTrue(self.value)


class SetupTest(unittest.TestCase):
    """ Tests that the setUp works correctly """
    def setUp(self):
        self.value = True

    def test_value_true(self):
        self.assertTrue(self.value)


class NoParallelClass(unittest.TestCase):
    __no_parallel__ = True

    @classmethod
    def setUpClass(cls):
        cls.value = True

    def test_one(self):
        self.assertTrue(self.value)
        self.value = False

    def test_two(self):
        self.assertFalse(self.value)
