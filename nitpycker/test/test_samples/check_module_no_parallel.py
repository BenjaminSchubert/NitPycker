"""
Test that modules that must not be run in parallel are indeed not run in parallel
"""


import time
import unittest


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"

__no_parallel__ = True


class Holder:
    """ dummy container """
    value = True


holder = Holder()


class NoParallelModule1(unittest.TestCase):
    def setUp(self):
        holder.value = True

    def test_one(self):
        self.assertTrue(holder.value)
        holder.value = False


class NoParallelModule2(unittest.TestCase):
    def test_two(self):
        time.sleep(0.5)
        self.assertFalse(holder.value)
