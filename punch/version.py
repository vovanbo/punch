# -*- coding: utf-8 -*-

import collections
from punch import version_part as vpart
from punch.helpers import import_file


class Version():

    def __init__(self):
        self.parts = collections.OrderedDict()

    @property
    def keys(self):
        return list(self.parts.keys())

    @property
    def values(self):
        return list(self.parts.values())

    def __eq__(self, other):
        return self.as_dict() == other.as_dict()

    def add_part(self, part):
        self.keys.append(part.name)
        self.parts[part.name] = part

    def create_part(self, name, value,
                    cls=vpart.IntegerVersionPart, *args, **kwds):
        self.keys.append(name)
        self.parts[name] = cls(name, value, *args, **kwds)

    def add_part_from_dict(self, dic):
        vp = vpart.VersionPart.from_dict(dic)
        self.keys.append(vp.name)
        self.parts[vp.name] = vp

    def get_part(self, name):
        return self.parts[name]

    def _reset_following_parts(self, name):
        idx = self.keys.index(name)
        reset_keys = self.keys[idx + 1:]
        for key in reset_keys:
            self.parts[key].reset()

    def inc(self, name):
        self.parts[name].inc()
        self._reset_following_parts(name)

    def set(self, adict):
        for key, value in adict.items():
            self.parts[key].set(value)

    def set_and_reset(self, name, value):
        self.parts[name].set(value)
        self._reset_following_parts(name)

    def copy(self):
        new = Version()
        for value in self.parts.values():
            new.add_part(value.copy())

        return new

    def as_dict(self):
        return dict((key, part.value) for key, part in self.parts.items())

    def as_list(self):
        return list((key, part.value) for key, part in self.parts.items())

    def to_file(self, version_filepath):
        with open(version_filepath, 'w') as f:
            for part in self.parts.values():
                f.write("{0.name} = {0!r}\n".format(part))

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
