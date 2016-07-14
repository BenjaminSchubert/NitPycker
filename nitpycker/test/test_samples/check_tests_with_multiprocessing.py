"""
Tests that we are able to use processes in tests without side effects
"""


from unittest import TestCase

from multiprocessing import Process, Pool


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class MultiprocessTest(TestCase):
    def test_process_launch(self):
        def noop():
            """ this doesn't do anything """
            pass

        p = Process(target=noop)
        p.start()
        p.join()

    def test_pool(self):
        with Pool() as f:
            f.map(sum, [[]])
