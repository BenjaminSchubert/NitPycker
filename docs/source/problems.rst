.. _problems:

================
Solving problems
================

Sometimes, some tests are required to run sequentially, or it is easier to have them run that way. For this, NitPycker
allows you to set a ``__no_parallel__ = True`` attribute to any module or class, and NitPycker will then run them as if
they were run by unittest, in the same order and the same way [#]_.

If however your tests are isolated and fail to run with NitPycker, please open an issue on the `issue tracker`_


.. _avoiding_problems:

Avoiding problems
-----------------

These are a few tips that can make you run into trouble is used with parallel tests:

    #. sharing variables between tests
    #. sharing resources (files)

If you can, you should avoid these, as they also do mean that the tests are not correctly isolated from each others


.. [#] In this, NitPycker takes the opposite paradigm compared to nose, which requires you to tell which testes can be run in parallel. Here, you tell which *cannot*

.. _issue tracker: #TODO
