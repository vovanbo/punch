# -*- coding: utf-8 -*-
import sys
from datetime import datetime

CALVER_SYNTAX = {
    'YYYY': {
        'fmt': '%Y',
        'strip': False
    },
    'YY': {
        'fmt': '%y',
        'strip': True
    },
    '0M': {
        'fmt': '%m',
        'strip': False
    },
    '0D': {
        'fmt': '%d',
        'strip': False
    },
    'MM': {
        'fmt': '%m',
        'strip': True
    },
    'DD': {
        'fmt': '%d',
        'strip': True
    }
}


def format_current_time(fmt):
    return datetime.now().strftime(fmt)


def strftime(fmt):
    newfmt = CALVER_SYNTAX.get(fmt, {'fmt': fmt, 'strip': False})
    value = format_current_time(newfmt['fmt'])

    if newfmt['strip']:
        return value.strip('0')

    return value


class VersionPart(object):
    @classmethod
    def factory(cls, **kwargs):
        part_type = kwargs.pop('type', 'integer')
        class_name = part_type.title().replace("_", "") + 'VersionPart'
        part_class = getattr(sys.modules[__name__], class_name)
        return part_class(**kwargs)


class IntegerVersionPart(VersionPart):
    def __init__(self, name, start_value=None, value=None, **kwargs):
        self.name = name
        self.start_value = 0 if start_value is None else int(start_value)
        self.value = self.start_value
        if value is not None:
            self.set(value)

    def inc(self):
        self.value += 1

    def set(self, value):
        self.value = int(value)

    def reset(self):
        self.value = self.start_value

    def copy(self):
        return IntegerVersionPart(self.name, start_value=self.start_value,
                                  value=self.value)


class ValueListVersionPart(VersionPart):
    def __init__(self, name, allowed_values, value=None, **kwargs):
        self.name = name
        self.allowed_values = [str(v) for v in allowed_values]
        self.value = self.allowed_values[0]
        if value is not None:
            self.set(value)

        # When copying this does not take the object itself
        self.values = [v for v in self.allowed_values]

    def set(self, value):
        if str(value) not in self.allowed_values:
            raise ValueError(
                "The given value {} is not allowed, "
                "the list of possible values is {}",
                value,
                self.allowed_values
            )
        self.value = str(value)

    def inc(self):
        idx = self.values.index(self.value)
        self.value = self.values[(idx + 1) % len(self.values)]

    def reset(self):
        self.value = self.values[0]

    def copy(self):
        return ValueListVersionPart(self.name, allowed_values=self.values,
                                    value=self.value)


class DateVersionPart(VersionPart):
    def __init__(self, name, fmt, value=None, **kwargs):
        self.name = name
        self.fmt = fmt

        if value is None:
            self.value = str(strftime(fmt))
        else:
            self.value = str(value)

    def reset(self):
        self.value = str(strftime(self.fmt))

    def inc(self):
        self.reset()

    def copy(self):
        return DateVersionPart(self.name, fmt=self.fmt, value=self.value)
