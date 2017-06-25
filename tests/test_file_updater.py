# coding: utf-8

import os
import pytest
import six

from punch.file_configuration import FileConfiguration
from punch.file_updater import FileUpdater
from punch.version import Version
from punch.version_part import IntegerVersionPart


@pytest.fixture
def current_version():
    v = Version()
    v.add_part(IntegerVersionPart(name='major', value=1))
    v.add_part(IntegerVersionPart(name='minor', value=2))
    v.add_part(IntegerVersionPart(name='patch', value=3))
    return v


@pytest.fixture
def new_patch_version():
    v = Version()
    v.add_part(IntegerVersionPart(name='major', value=1))
    v.add_part(IntegerVersionPart(name='minor', value=2))
    v.add_part(IntegerVersionPart(name='patch', value=4))
    return v


@pytest.fixture
def new_minor_version():
    v = Version()
    v.add_part(IntegerVersionPart(name='major', value=1))
    v.add_part(IntegerVersionPart(name='minor', value=3))
    v.add_part(IntegerVersionPart(name='patch', value=0))
    return v


@pytest.fixture
def temp_dir_with_version_file(temp_empty_dir):
    with open(os.path.join(temp_empty_dir, "__init__.py"), 'w') as f:
        f.write("__version__ = \"1.2.3\"")

    return temp_empty_dir


@pytest.fixture
def temp_dir_with_unicode_file(temp_empty_dir):
    with open(os.path.join(temp_empty_dir, "__init__.py"), 'w') as f:
        f.write("__version⚠__ = \"1.2.3\"")

    return temp_empty_dir


@pytest.fixture
def temp_dir_with_version_file_partial(temp_empty_dir):
    with open(os.path.join(temp_empty_dir, "__init__.py"), 'w') as f:
        f.write("__version__ = \"1.2\"")

    return temp_empty_dir


def test_file_updater(temp_dir_with_version_file, current_version,
                      new_patch_version):
    filepath = os.path.join(temp_dir_with_version_file, "__init__.py")

    local_variables = {
        'serializer': "__version__ = \"{{major}}.{{minor}}.{{patch}}\""
    }

    file_config = FileConfiguration(filepath, local_variables)

    updater = FileUpdater(file_config)
    updater(current_version, new_patch_version)

    with open(filepath, 'r') as f:
        new_file_content = f.read()

    assert new_file_content == "__version__ = \"1.2.4\""


def test_file_updater_with_unicode_characters(temp_dir_with_unicode_file,
                                              current_version,
                                              new_patch_version):
    filepath = os.path.join(temp_dir_with_unicode_file, "__init__.py")

    local_variables = {
        'serializer': "__version⚠__ = \"{{major}}.{{minor}}.{{patch}}\""
    }

    file_config = FileConfiguration(filepath, local_variables)

    updater = FileUpdater(file_config)
    updater(current_version, new_patch_version)

    with open(filepath, 'r') as f:
        new_file_content = f.read()

    assert new_file_content == "__version⚠__ = \"1.2.4\""


def test_file_updater_with_partial_serializer(
        temp_dir_with_version_file_partial,
        current_version, new_minor_version):
    filepath = os.path.join(temp_dir_with_version_file_partial, "__init__.py")

    local_variables = {
        'serializer': "__version__ = \"{{major}}.{{minor}}\""
    }

    file_config = FileConfiguration(filepath, local_variables)

    updater = FileUpdater(file_config)
    updater(current_version, new_minor_version)

    with open(filepath, 'r') as f:
        new_file_content = f.read()

    assert new_file_content == "__version__ = \"1.3\""


def test_file_updater_with_nonexisting_file(temp_empty_dir, current_version,
                                            new_minor_version):
    filepath = os.path.join(temp_empty_dir, "__init__.py")
    local_variables = {
        'serializer': "__version__ = \"{{major}}.{{minor}}\""
    }

    file_config = FileConfiguration(filepath, local_variables)

    if six.PY2:
        expected_exception = IOError
    else:
        expected_exception = FileNotFoundError

    with pytest.raises(expected_exception) as exc:
        updater = FileUpdater(file_config)
        updater(current_version, new_minor_version)

    assert str(exc.value) == "The file {} does not exist".format(
        file_config.path)


def test_file_updater_preview(temp_empty_dir, current_version,
                              new_minor_version):
    filepath = os.path.join(temp_empty_dir, "__init__.py")
    local_variables = {
        'serializer': "__version__ = \"{{major}}.{{minor}}\""
    }

    file_config = FileConfiguration(filepath, local_variables)

    updater = FileUpdater(file_config)
    summary = updater.get_summary(current_version, new_minor_version)

    assert summary == [("__version__ = \"1.2\"", "__version__ = \"1.3\"")]
