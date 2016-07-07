=========
Nitpycker
=========

NitPycker is a improved runner for your tests in Python. It allows your tests to run in parallel in a way totally
transparent for you.

For a quick jump start, please see :ref:`quickstart`, for more information please read :ref:`why_nitpycker`.

However, be warned that if you have tests that depend on each others, or tests fixtures that prevent the use of
multiprocessing, some tests will fail. This is *not* a bug in NitPycker. You can still use nitpycker if you have only
a few problems. For this, please see :ref:`avoiding_problems`.


.. _why_nitpycker:

Why NitPycker ?
---------------

I created NitPycker because running Python unittest in a multithreaded environment was impossible for me. I had a heavy
test suite (>90 tests) with integration tests, and running them sequentially would take more than 8 hours.
With NitPycker, time got down to 40 minutes.

Other Python testing framework do also provide multithreaded tests, such as py.test, nose and nose2. However, they all
have some problems when running in multithreaded environment (code coverage incorrect, path manipulation, deadlocks)
meaning that they are not perfect for it. NitPycker is created with multiprocess *in mind*, meaning a better integration
and more reliable results. If tests are *independent* and work with Python's unittest, Nitpycker will be fully compatible
with them [#]_.



.. _quickstart:

Quickstart
----------

Getting started is trivial :

#. Download NitPycker from the NitPycker page on the Python Package Index or by using ``pip install nitpycker``.

#. Use ``nitpycker`` to run your tests

    .. code-block:: console

        $ nitpycker [options] [args] directory


Getting help
------------

Bug reports are welcome on the GitHub's project's `issue tracker`_


More information
----------------

..  toctree::
    :maxdepth: 1

    cmd
    coverage
    problems


.. _issue tracker: https://github.com/BenjaminSchubert/NitPycker/issues
.. _open an issue: https://github.com/BenjaminSchubert/NitPycker/issues

.. [#] if it's not, please `open an issue`_, this should get fixed !
