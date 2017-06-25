# -*- coding: utf-8 -*-
from collections import OrderedDict

from punch.version_part import IntegerVersionPart


class Version(OrderedDict):
    def __eq__(self, other):
        if isinstance(other, Version):
            return tuple(self.simplify()) == tuple(other.simplify())
        return super(Version, self).__eq__(other)

    def add_part(self, part):
        self[part.name] = part

    def create_part(self, name, cls=IntegerVersionPart, **kwargs):
        self[name] = cls(name, **kwargs)

    def get_part(self, name):
        return self[name]

    def _reset_following_parts(self, name):
        reset = False
        for part_name in self.keys():
            if reset:
                self[part_name].reset()
            elif part_name == name:
                reset = True

    def inc(self, name):
        self[name].inc()
        self._reset_following_parts(name)

    def set(self, adict):
        for key, value in adict.items():
            self[key].set(value)

    def set_and_reset(self, name, value):
        self[name].set(value)
        self._reset_following_parts(name)

    def copy(self):
        new = Version()
        for value in self.values():
            new.add_part(value.copy())
        return new

    def simplify(self):
        for name, part in self.items():
            yield name, part.value
