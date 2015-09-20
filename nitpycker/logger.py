#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Logging helpers for NitPycker
"""


import logging

__author__ = "Benjamin Schubert, ben.c.schubert@gmail.com"


def setup_logger(name: str) -> logging.Logger:
    """
    Sets up a logger for the given name

    :param name: name of the logger
    :return: logger
    """
    logger = logging.getLogger(name)
    formatter = logging.Formatter("%(levelname)s:%(name)s: %(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
