"""
Tests to check that NitPycker's tests are isolated in different process to limit side-effects
"""


import unittest


__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


class ParallelClass(unittest.TestCase):
    value = 0

    @classmethod
    def setUp(cls):
        cls.value += 1

    def test_one(self):
        self.assertEqual(self.value, 1)

    def test_two(self):
        self.assertEqual(self.value, 1)
