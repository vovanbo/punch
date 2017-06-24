import json
import subprocess
import pytest

pytestmark = pytest.mark.slow

config_file_content = json.dumps({
    'format': 1,
    'globals': {
        'serializer': '{{date}}',
    },
    'files': ['README.md'],
    'actions': {
        'mbuild': {
            'type': 'conditional_reset',
            'field': 'build',
            'update_fields': ['year', 'month']
        }
    },
    'version': {
        'variables': [
            {
                'name': 'date',
                'type': 'date',
                'fmt': '%Y%m%d'
            }
        ],
        'values': ['20160415']
    }
})


def test_update_date(test_environment, mocker):
    test_environment.ensure_file_is_present("README.md", "Version 20160415.")
    test_environment.ensure_file_is_present("punch.json", config_file_content)

    system_date = subprocess.check_output(['date', '+%Y%m%d'])
    system_date = system_date.decode('utf8').replace('\n', '')

    test_environment.call(["punch", "--part", "date"])

    assert test_environment.get_file_content("README.md") == \
        "Version {}.".format(system_date)
