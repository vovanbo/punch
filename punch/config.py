import collections
import json

import six

from punch.file_configuration import FileConfiguration
from punch.version import Version
from punch.version_part import VersionPart, IntegerVersionPart


class ConfigurationVersionError(Exception):
    """
    An exception used to signal that the configuration file version is wrong
    """


class PunchConfig(object):
    def __init__(self, config_filepath):
        configuration = json.load(config_filepath)

        assert 'format' in configuration, \
            "Given config file is invalid: missing 'format' variable"

        self.__config_version__ = configuration['format']
        if self.__config_version__ > 1:
            raise ConfigurationVersionError(
                "Unsupported configuration file version "
                "{}".format(self.__config_version__)
            )

        self.globals = configuration.get('globals', {})

        assert 'files' in configuration, \
            "Given config file is invalid: missing 'files' attribute"

        files = configuration['files']
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

        assert 'version' in configuration, \
            "Given config file is invalid: missing 'version' attribute"
        assert 'variables' in configuration['version'], \
            "Variables is required in version configuration."
        assert 'current' in configuration['version'], \
            "Current version is not found in configuration."

        self.version = Version()
        for variable, value in zip(configuration['version']['variables'],
                                   configuration['version']['current']):
            if isinstance(variable, six.string_types):
                self.version.add_part(IntegerVersionPart(name=variable,
                                                         value=value))
            elif isinstance(variable, collections.MutableMapping):
                part = VersionPart.from_dict(variable)
                part.set(value)
                self.version.add_part(part)

        self.vcs = configuration.get('vcs')
        if self.vcs is not None and 'name' not in self.vcs:
            raise ValueError("Missing key 'name' in VCS configuration")

        self.actions = configuration.get('actions', {})
