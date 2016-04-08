#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def non_private_exit(code):
    try:
        sys.stdin.close()
    except:
        pass
    raise SystemExit(code)


class FrozenFCode:
    def __init__(self, f_code):
        self.__co_filename = f_code.co_filename
        self.__co_name = f_code.co_name

    @property
    def co_filename(self):
        return self.__co_filename

    @property
    def co_name(self):
        return self.__co_name


class FrozenTbFrame:
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
        return self.__f_globals

    @property
    def f_code(self):
        return self.__f_code


class FrozenTraceback:
    __tb_next = None

    def __init__(self, tb):
        self.__tb_frame = FrozenTbFrame(tb.tb_frame)
        self.__tb_lineno = tb.tb_lineno
        if tb.tb_next is not None:
            self.__tb_next = FrozenTraceback(tb.tb_next)

    @property
    def tb_frame(self):
        return self.__tb_frame

    @property
    def tb_next(self):
        return self.__tb_next

    @property
    def tb_lineno(self):
        return self.__tb_lineno


class FrozenExcInfo:
    def __init__(self, exc_info):
        quit = non_private_exit
        exit = non_private_exit
        self.infos = exc_info[:2] + (FrozenTraceback(exc_info[2]),)

    def __getitem__(self, item):
        return self.infos[item]

    def __iter__(self):
        for i in self.infos:
            yield i
