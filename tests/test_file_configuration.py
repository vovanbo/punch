import pytest

from punch.file_configuration import FileConfiguration


@pytest.fixture
def global_variables():
    return {
        'serializer': '{{ major }}.{{ minor }}.{{ patch }}',
        'mark': 'just a mark'
    }


@pytest.fixture
def local_variables():
    return {
        'serializer': '{{ major }}.{{ minor }}'
    }


@pytest.fixture
def file_configuration_dict():
    return {
        'path': 'pkg/__init__.py',
        'serializer': '{{ major }}.{{ minor }}'
    }


def test_file_configuration_from_string_local_variables_take_precedence(
        local_variables, global_variables):
    fconf = FileConfiguration(
        'pkg/__init__.py',
        local_variables,
        global_variables
    )

    assert fconf.path == 'pkg/__init__.py'
    assert fconf.config['serializer'] == '{{ major }}.{{ minor }}'
    assert fconf.config['mark'] == 'just a mark'


def test_file_configuration_from_string_can_include_global_variables(
        global_variables):
    local_variables = {
        'serializer': '__version__ = {{GLOBALS.serializer}}'
    }
    fconf = FileConfiguration(
        'pkg/__init__.py',
        local_variables,
        global_variables
    )

    assert fconf.path == 'pkg/__init__.py'
    assert fconf.config['serializer'] == \
        '__version__ = {{ major }}.{{ minor }}.{{ patch }}'
    assert fconf.config['mark'] == 'just a mark'


def test_file_conf_fr_str_path_cannot_be_overridden_by_global_variables(
        local_variables, global_variables):
    global_variables['path'] = 'a/new/path'
    fconf = FileConfiguration(
        'pkg/__init__.py',
        local_variables,
        global_variables
    )

    assert fconf.path == 'pkg/__init__.py'


def test_file_conf_fr_str_path_cannot_be_overridden_by_local_variables(
        local_variables, global_variables):
    local_variables['path'] = 'a/new/path'
    fconf = FileConfiguration(
        'pkg/__init__.py',
        local_variables,
        global_variables
    )

    assert fconf.path == 'pkg/__init__.py'


def test_file_configuration_from_dict_local_variables_take_precedence(
        file_configuration_dict, global_variables):
    fconf = FileConfiguration(
        path=file_configuration_dict['path'],
        local_variables=file_configuration_dict,
        global_variables=global_variables
    )

    assert fconf.path == 'pkg/__init__.py'
    assert fconf.config['serializer'] == '{{ major }}.{{ minor }}'
    assert fconf.config['mark'] == 'just a mark'


def test_file_conf_fr_dict_path_cannot_be_overridden_by_global_variables(
        file_configuration_dict, global_variables):
    global_variables['path'] = 'a/new/path'
    fconf = FileConfiguration(
        path=file_configuration_dict['path'],
        local_variables=file_configuration_dict,
        global_variables=global_variables
    )

    assert fconf.path == 'pkg/__init__.py'
