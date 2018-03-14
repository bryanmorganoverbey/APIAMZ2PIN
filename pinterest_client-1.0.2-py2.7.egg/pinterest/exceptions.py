# -*- coding: utf-8 -*-


class PinterestException(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)


class PinterestRequestException(PinterestException):
    def __init__(self, *args):
        PinterestException.__init__(self, *args)


class PinterestLoginFailedException(PinterestException):
    def __init__(self, *args):
        PinterestException.__init__(self, *args)


class PinterestLoginRequiredException(PinterestException):
    def __init__(self, *args):
        PinterestException.__init__(self, *args)
