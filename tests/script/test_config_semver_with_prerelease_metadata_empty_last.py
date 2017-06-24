import json

import pytest

pytestmark = pytest.mark.slow

config = {
    'format': 1,
    'globals': {
        'serializer':
            "{{ major }}.{{ minor }}.{{ patch }}"
            "{{ '-{}'.format(prerelease) if prerelease }}",
    },
    'files': ['README.md'],
    'version': {
        'variables': [
            'major',
            'minor',
            'patch',
            {
                'name': 'prerelease',
                'type': 'value_list',
                'allowed_values': ['alpha', 'beta', '']
            }
        ],
        'values': ['1', '0', '0', 'alpha']
    }
}
config_file_content = json.dumps(config)


def test_update_major(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0-alpha")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "major"])
    assert test_environment.get_file_content("README.md") == \
        "Version 2.0.0-alpha"


def test_update_minor(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0-alpha")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "minor"])
    assert test_environment.get_file_content("README.md") == \
        "Version 1.1.0-alpha"


def test_update_patch(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0-alpha")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "patch"])
    assert test_environment.get_file_content("README.md") == \
        "Version 1.0.1-alpha"


def test_update_prerelease(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0-alpha")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "prerelease"])
    assert test_environment.get_file_content("README.md") == \
        "Version 1.0.0-beta"


def test_update_after_last_prerelease(test_environment):
    config['version']['values'] = ['1', '0', '0', 'beta']
    config_file_content = json.dumps(config)
    test_environment.ensure_file_is_present("README.md", "Version 1.0.0-beta")
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    test_environment.call(["punch", "--part", "prerelease"])
    assert test_environment.get_file_content("README.md") == "Version 1.0.0"
