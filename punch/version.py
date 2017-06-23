# -*- coding: utf-8 -*-

import collections
import operator
from collections import OrderedDict

from punch.version_part import VersionPart, IntegerVersionPart
from punch.helpers import import_file


class Version(OrderedDict):
    def __eq__(self, other):
        if isinstance(other, Version):
            return tuple(self.simplify()) == tuple(other.simplify())
        return super(Version, self).__eq__(other)

    def add_part(self, part):
        self[part.name] = part

    def create_part(self, name, value,
                    cls=IntegerVersionPart, *args, **kwds):
        self[name] = cls(name, value, *args, **kwds)

    def add_part_from_dict(self, dic):
        vp = VersionPart.from_dict(dic)
        self[vp.name] = vp

    def get_part(self, name):
        return self[name]

    def _reset_following_parts(self, name):
        reset = False
        for part_name in self.keys():
            if reset:
                self[part_name].reset()
            elif part_name == name:
                reset = True
        # idx = operator.indexOf(self.keys(), name)
        # reset_keys = self.keys()[idx + 1:]
        # for key in reset_keys:
        #     self[key].reset()

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

    @classmethod
    def from_file(cls, version_filepath, version_description):
        version_module = import_file(version_filepath)
        version = Version()

        for version_part in version_description:
            if isinstance(version_part, collections.Mapping):
                version_part_name = version_part['name']
                version_part['value'] = cls._get_version_part(
                    version_module, version_part, version_part_name)
                version.add_part_from_dict(version_part)
            else:
                version_part_name = version_part
                version_part_value = cls._get_version_part(
                    version_module, version_part, version_part_name)
                version.create_part(version_part_name, version_part_value)

        return version

    @classmethod
    def _get_version_part(cls, version_module,
                          version_part, version_part_name):
        try:
            return getattr(version_module, version_part_name)
        except AttributeError:
            raise ValueError(
                "Given version file is invalid:" +
                " missing '{}' variable".format(version_part_name)
            )
