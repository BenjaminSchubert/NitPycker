"""
Various classes and functions to make some part of the tests serializable

This is needed because these information are required for the test results
to be meaningful
"""


import sys

import builtins


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def non_private_exit(code=0):
    """
    patch for the builtin quit and exit function to
    allow to serialize objects that uses them

    :param code: error code with with to exit
    """
    # noinspection PyBroadException
    try:
        sys.stdin.close()
    except:
        pass
    raise SystemExit(code)


class FrozenFCode:
    """
    Code object that can be serialized

    :param f_code: original code object
    """
    def __init__(self, f_code):
        self.__co_filename = f_code.co_filename
        self.__co_name = f_code.co_name

    @property
    def co_filename(self):
        """ name of the file of the code object """
        return self.__co_filename

    @property
    def co_name(self):
        """ name of the code object """
        return self.__co_name


class FrozenTbFrame:
    """
    Traceback frame that can be serialized

    This will remove some parts of the traceback that are not serializable,
    so the frozen frame might not be complete.

    :param tb_frame: original traceback frame
    """
    def __init__(self, tb_frame):
        self.__f_globals = tb_frame.f_globals.copy()
        self.__f_code = FrozenFCode(tb_frame.f_code)
        to_remove = []
        for key, item in self.__f_globals.items():
            if "module" in str(item):
                to_remove.append(key)

        for key in to_remove:
            self.__f_globals.pop(key)

    @property
    def f_globals(self):
        """ globals contained in the frame """
        return self.__f_globals

    @property
    def f_code(self):
        """ code object executed in the frame """
        return self.__f_code


class FrozenTraceback:
    """
    Traceback that can be serialized

    This class lacks some features of the original traceback,
    they can be implemented on demand

    :param tb: original traceback
    """
    __tb_next = None

    def __init__(self, tb):
        self.__tb_frame = FrozenTbFrame(tb.tb_frame)
        self.__tb_lineno = tb.tb_lineno
        if tb.tb_next is not None:
            self.__tb_next = FrozenTraceback(tb.tb_next)

    @property
    def tb_frame(self):
        """ traceback frame """
        return self.__tb_frame

    @property
    def tb_next(self):
        """ next traceback """
        return self.__tb_next

    @property
    def tb_lineno(self):
        """ line number of the traceback """
        return self.__tb_lineno


class FrozenExcInfo:
    """
    Execution information that can be serialized

    :param exc_info: original execution information
    """
    def __init__(self, exc_info):
        builtins.quit = non_private_exit
        builtins.exit = non_private_exit
        self.infos = exc_info[:2] + (FrozenTraceback(exc_info[2]),)

    def __getitem__(self, item):
        return self.infos[item]

    def __iter__(self):
        for i in self.infos:
            yield i
