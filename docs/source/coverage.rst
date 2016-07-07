.. _coverage:

=============
Test coverage
=============

NitPycker can be used with Coverage.py. You will however need to create a ``.coveragerc`` file in the directory from
which you run your tests.

This file needs to contain all information about how coverage should run. This is needed as processes need to get access
to this information and it is for now not possible through the command line.

One thing that is absolutely needed to have meaningful results is to add

``concurrency = multiprocessing`` in the ``[run]`` section as nitpycker uses the multiprocessing package


An example of .coveragerc file is given `here <https://github.com/BenjaminSchubert/NitPycker/blob/master/.coveragerc>`_
