# -*- coding: utf-8 -*-


class Currency(object):
        def __init__(self, precision, value, value_int):
            self.precision = precision
            self.value = value
            self.value_int = value_int

        def to_data(self, name):
            return {"%s[precision]" % name: self.precision,
                    "%s[value]" % name: self.value,
                    "%s[value_int]" % name: self.value_int}