import json

import pytest

pytestmark = pytest.mark.slow

config_file_content = json.dumps({
    'format': 1,
    'globals': {
        'serializer':
            "{{ major }}.{{ minor }}.{{ patch }}+{{ '{0:03d}'.format(build) }}"
    },
    'files': ['README.md'],
    'version': {
        'variables': [
            'major',
            'minor',
            'patch',
            {
                'name': 'build',
                'type': 'integer',
                'start_value': 1
            }
        ],
        'values': ['1', '0', '0', '1']
    }
})


def test_update_major(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0+001")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "major"])
    assert test_environment.get_file_content("README.md") == \
        "Version 2.0.0+001"


def test_update_minor(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0+001")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "minor"])
    assert test_environment.get_file_content("README.md") == \
        "Version 1.1.0+001"


def test_update_patch(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0+001")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "patch"])
    assert test_environment.get_file_content("README.md") == \
        "Version 1.0.1+001"


def test_update_build(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0+001")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "build"])
    assert test_environment.get_file_content("README.md") == \
        "Version 1.0.0+002"
