"""
This checks that a non-serializable test is indeed reported
"""


import unittest
import threading


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class SerializationTest(unittest.TestCase):
    def test_serialization(self):
        self.l = threading.Lock()
