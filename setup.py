#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Setup declaration to install NitPycker
"""

params = dict(
    name='NitPycker',
    version='0.1',
    packages=['nitpycker', 'nitpycker.plugins'],
    url='https://github.com/BenjaminSchubert/NitPycker',
    download_url="https://github.com/BenjaminSchubert/NitPycker/tar.gz/0.1",
    license='MIT',
    author='Benjamin Schubert',
    author_email='ben.c.schubert@gmail.com',
    description='A multithreaded test runner',

    classifiers=[
        "Topic :: Software Development :: Testing",
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5"
    ],

    extras_require={
        'coverage': ["coverage"]
    }
)

with open("README.rst") as _desc:
    params["long_description"] = _desc.read()

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

else:
    params['entry_points'] = {
        'console_scripts': [
            "nitpycker = nitpycker:run"
        ]
    }

setup(**params)
