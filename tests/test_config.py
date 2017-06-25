import json
import os
from copy import copy

import sys

from punch.action import RefreshAction

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

import pytest

from punch.config import PunchConfig, ConfigurationVersionError

CONFIG_FILE_CONTENT = {
    'format': 1,
    'globals': {
        'serializer': '{{major}}.{{minor}}.{{patch}}'
    },
    'files': [
        'pkg/__init__.py',
        {
            'path': 'version.txt',
            'serializer': '{{major}}.{{minor}}'
        }
    ],
    'version': {
        'variables': [
            {
                'name': 'major',
                'type': 'integer'
            },
            {
                'name': 'minor',
                'type': 'integer'
            },
            {
                'name': 'patch',
                'type': 'integer'
            }
        ],
        'values': ['1', '5', '0']
    },
}
CONFIG_FILE_CONTENT_ACTIONS = {
    'mbuild': {
        'type': 'refresh',
        'refresh_fields': ['year', 'month'],
        'fallback_field': 'build'
    }
}
CONFIG_FILE_CONTENT_VCS = {
    'name': 'git',
    'commit_message': "Version updated to {{ new_version }}",
    'options': {
        'make_release_branch': False,
        'annotate_tags': False,
        'annotation_message': '',
    }
}
CONFIG_FILE_CONTENT_WRONG_VCS = {
    'commit_message': "Version updated to {{ new_version }}",
    'options': {
        'make_release_branch': False,
        'annotate_tags': False,
        'annotation_message': '',
    }
}


@pytest.fixture
def config_file_content():
    return json.dumps(CONFIG_FILE_CONTENT)


@pytest.fixture
def config_file_content_with_actions():
    content = copy(CONFIG_FILE_CONTENT)
    content['actions'] = CONFIG_FILE_CONTENT_ACTIONS
    return json.dumps(content)


@pytest.fixture
def config_file_content_with_vcs():
    content = copy(CONFIG_FILE_CONTENT)
    content['vcs'] = CONFIG_FILE_CONTENT_VCS
    return json.dumps(content)


@pytest.fixture
def config_file_content_with_wrong_vcs():
    content = copy(CONFIG_FILE_CONTENT)
    content['vcs'] = CONFIG_FILE_CONTENT_WRONG_VCS
    return json.dumps(content)


@pytest.fixture
def empty_file_content():
    return ''


@pytest.fixture
def illegal_config_file_content():
    return json.dumps({'format': 2})


@pytest.fixture
def config_file_name():
    return 'punch.json'


def write_file(dir, content, config_file_name):
    with open(os.path.join(dir, config_file_name), 'w') as f:
        f.write(content)


def test_config_file_not_found():
    wrong_file = 'not_found_config_file.json'
    if sys.version_info < (3,):
        with pytest.raises(IOError):
            PunchConfig(wrong_file)
    else:
        with pytest.raises(FileNotFoundError):
            PunchConfig(wrong_file)


def test_read_empty_config_file(temp_empty_dir, empty_file_content,
                                config_file_name):
    write_file(temp_empty_dir, empty_file_content, config_file_name)

    with pytest.raises(JSONDecodeError) as exc:
        PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    if sys.version_info < (3, 4):
        assert str(exc.value) == "No JSON object could be decoded"
    else:
        assert str(exc.value) == "Expecting value: line 1 column 1 (char 0)"


def test_read_illegal_config_file(temp_empty_dir, illegal_config_file_content,
                                  config_file_name):
    write_file(temp_empty_dir, illegal_config_file_content, config_file_name)

    with pytest.raises(ConfigurationVersionError) as exc:
        PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    assert str(exc.value) == "Unsupported configuration file version 2"


def test_read_plain_variables(temp_empty_dir, config_file_content,
                              config_file_name):
    write_file(temp_empty_dir, config_file_content, config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))
    assert cf.format == 1


def test_read_global_variables(temp_empty_dir, config_file_content,
                               config_file_name):
    write_file(temp_empty_dir, config_file_content, config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    expected_dict = {
        'serializer': '{{major}}.{{minor}}.{{patch}}'
    }

    assert cf.globals == expected_dict


def test_read_files(temp_empty_dir, config_file_content, config_file_name):
    write_file(temp_empty_dir, config_file_content, config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    assert len(cf.files) == 2
    assert [fc.path for fc in cf.files] == ['pkg/__init__.py', 'version.txt']


def test_read_version(temp_empty_dir, config_file_content, config_file_name):
    write_file(temp_empty_dir, config_file_content, config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    expected_value = [
        {
            'name': 'major',
            'type': 'integer'
        },
        {
            'name': 'minor',
            'type': 'integer'
        },
        {
            'name': 'patch',
            'type': 'integer'
        }
    ]

    assert cf._variables == expected_value


def test_read_config_missing_vcs(temp_empty_dir, config_file_content,
                                 config_file_name):
    write_file(temp_empty_dir, config_file_content, config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))
    assert cf.vcs is None


def test_read_vcs(temp_empty_dir, config_file_content_with_vcs,
                  config_file_name):
    write_file(temp_empty_dir, config_file_content_with_vcs, config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    expected_dict = {
        'name': 'git',
        'commit_message': "Version updated to {{ new_version }}",
        'options': {
            'make_release_branch': False,
            'annotate_tags': False,
            'annotation_message': '',
        }
    }

    assert cf.vcs == expected_dict


def test_read_vcs_missing_name(temp_empty_dir,
                               config_file_content_with_wrong_vcs,
                               config_file_name):
    write_file(temp_empty_dir, config_file_content_with_wrong_vcs,
               config_file_name)
    with pytest.raises(ValueError) as exc:
        PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    assert str(exc.value) == "Missing key 'name' in VCS configuration"


def test_read_empty_actions(temp_empty_dir, config_file_content,
                            config_file_name):
    write_file(temp_empty_dir, config_file_content,
               config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    expected_value = {}

    assert cf.actions == expected_value


def test_read_actions(temp_empty_dir, config_file_content_with_actions,
                      config_file_name):
    write_file(temp_empty_dir, config_file_content_with_actions,
               config_file_name)
    cf = PunchConfig(os.path.join(temp_empty_dir, config_file_name))

    expected_action = RefreshAction(refresh_fields=['year', 'month'],
                                    fallback_field='build')

    assert 'mbuild' in cf.actions

    cf_action = cf.actions['mbuild']
    assert cf_action.refresh_fields == expected_action.refresh_fields
    assert cf_action.fallback_field == expected_action.fallback_field
