"""
Test that class that must not be run in parallel are indeed not run in parallel
"""


import time
import unittest


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class Holder:
    """ dummy container """
    value = True


class NoParallelClass(unittest.TestCase):
    """
    Class with tests that should fail if run in parallel
    """
    __no_parallel__ = True

    @classmethod
    def setUpClass(cls):
        cls.holder = Holder()

    def test_one(self):
        self.assertTrue(self.holder.value)
        self.holder.value = False

    def test_two(self):
        time.sleep(0.5)
        self.assertFalse(self.holder.value)
