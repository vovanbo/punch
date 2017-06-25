import json
import subprocess

import pytest

pytestmark = pytest.mark.slow


def test_punch_version_flag(test_environment):
    # output = test_environment_fixture.output(["punch", "--version"])

    # Punch version 1.0.1
    # Copyright (C) 2016 Leonardo Giordani

    expected_output = """
    Copyright \(C\) \d{4}\-\d{4} Leonardo Giordani
    This is free software, see the LICENSE file.
    Source: https://github.com/lgiordani/punch
    Documentation: http://punch.readthedocs.io/en/latest/
    """

    test_environment.compare_output(expected_output, ["punch", "--version"])


def test_punch_increase_version_part(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0")
    config = {
        'format': 1,
        'globals': {
            'serializer': '{{major}}.{{minor}}.{{patch}}',
        },
        'files': ['README.md'],
        'version': {
            'variables': ['major', 'minor', 'patch'],
            'values': ['1', '0', '0']
        }
    }
    config_file_content = json.dumps(config)
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "major"])
    assert test_environment.get_file_content("README.md") == "Version 2.0.0"


def test_punch_set_version_part(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0")
    config = {
        'format': 1,
        'globals': {
            'serializer': '{{major}}.{{minor}}.{{patch}}',
        },
        'files': ['README.md'],
        'version': {
            'variables': ['major', 'minor', 'patch'],
            'values': ['1', '0', '0']
        }
    }
    config_file_content = json.dumps(config)
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--set-part", "minor=4"])
    assert test_environment.get_file_content("README.md") == "Version 1.4.0"


def test_punch_set_multiple_version_parts(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0")
    config = {
        'format': 1,
        'globals': {
            'serializer': '{{major}}.{{minor}}.{{patch}}',
        },
        'files': ['README.md'],
        'version': {
            'variables': ['major', 'minor', 'patch'],
            'values': ['1', '0', '0']
        }
    }
    config_file_content = json.dumps(config)
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--set-part", "minor=4,patch=23"])
    assert test_environment.get_file_content("README.md") == "Version 1.4.23"


def test_punch_set_and_reset_single_part(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.2.3")
    config = {
        'format': 1,
        'globals': {
            'serializer': '{{major}}.{{minor}}.{{patch}}',
        },
        'files': ['README.md'],
        'version': {
            'variables': ['major', 'minor', 'patch'],
            'values': ['1', '2', '3']
        }
    }
    config_file_content = json.dumps(config)
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--set-part", "major=9", "--reset-on-set"])
    assert test_environment.get_file_content("README.md") == "Version 9.0.0"


def test_punch_set_and_reset_multiple_parts_fails(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.2.3")
    config = {
        'format': 1,
        'globals': {
            'serializer': '{{major}}.{{minor}}.{{patch}}',
        },
        'files': ['README.md'],
        'version': {
            'variables': ['major', 'minor', 'patch'],
            'values': ['1', '2', '3']
        }
    }
    config_file_content = json.dumps(config)
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    with pytest.raises(subprocess.CalledProcessError):
        test_environment.output(
            ["punch", "--set-part", "major=9,minor=8", "--reset-on-set"])
