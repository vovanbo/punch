import collections
import json
from copy import copy

import six

from punch.action import Action
from punch.file_configuration import FileConfiguration
from punch.version import Version
from punch.version_part import VersionPart, IntegerVersionPart


class ConfigurationVersionError(Exception):
    """
    An exception used to signal that the configuration file version is wrong
    """


class PunchConfig(object):
    def __init__(self, source):
        with open(source) as f:
            self._configuration = json.load(f)

        self._source = source

        assert 'format' in self._configuration, \
            "Given config file is invalid: missing 'format' variable"

        self.format = self._configuration['format']
        if self.format > 1:
            raise ConfigurationVersionError(
                "Unsupported configuration file version "
                "{}".format(self.format)
            )

        self.globals = self._configuration.get('globals', {})

        assert 'files' in self._configuration, \
            "Given config file is invalid: missing 'files' attribute"

        files = self._configuration['files']
        self.files = []
        for file_configuration in files:
            if isinstance(file_configuration, collections.Mapping):
                self.files.append(
                    FileConfiguration.from_dict(file_configuration,
                                                self.globals)
                )
            else:
                self.files.append(
                    FileConfiguration(file_configuration, {}, self.globals)
                )

        assert 'version' in self._configuration, \
            "Given config file is invalid: missing 'version' attribute"
        assert 'variables' in self._configuration['version'], \
            "Variables is required in version configuration."
        assert 'values' in self._configuration['version'], \
            "Current version is not found in configuration."

        self.version = Version()
        self._variables = self._configuration['version']['variables']
        self._values = self._configuration['version']['values']
        for variable, value in zip(self._variables, self._values):
            if isinstance(variable, six.string_types):
                self.version.add_part(IntegerVersionPart(name=variable,
                                                         value=value))
            elif isinstance(variable, collections.MutableMapping):
                part = VersionPart.factory(value=value, **variable)
                self.version.add_part(part)

        self.vcs = self._configuration.get('vcs')
        if self.vcs is not None and 'name' not in self.vcs:
            raise ValueError("Missing key 'name' in VCS configuration")

        actions = self._configuration.get('actions', {})
        self.actions = {k: Action.factory(**v) for k, v in actions.items()}

    def dump(self, version=None, target=None, verbose=False):
        assert isinstance(version, Version), 'Version instance is required.'

        target = self._source if target is None else target

        new_configuration = copy(self._configuration)
        new_configuration['version']['current'] = \
            [str(p.value) for p in version.values()]

        with open(target, 'w') as f:
            if verbose:
                print("* Updating punch file")
            json.dump(new_configuration, f)
