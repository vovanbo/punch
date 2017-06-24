import json
import subprocess
import pytest

pytestmark = pytest.mark.slow

system_year = subprocess.check_output(['date', '+%Y'])
system_year = system_year.decode('utf8').replace('\n', '')

system_month = subprocess.check_output(['date', '+%m'])
system_month = system_month.decode('utf8').replace('\n', '')


config_file_content = json.dumps({
    'format': 1,
    'globals': {
        'serializer': '{{year}}.{{month}}.{{build}}',
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
                'name': 'year',
                'type': 'date',
                'fmt': '%Y'
            },
            {
                'name': 'month',
                'type': 'date',
                'fmt': '%m'
            },
            'build'
        ],
        'values': [system_year, system_month, '0']
    }
})


def test_action_refresh(script_runner, test_environment):
    test_environment.ensure_file_is_present(
        "README.md",
        "Version {}.{}.0.".format(system_year, system_month)
    )
    test_environment.ensure_file_is_present("punch.json", config_file_content)
    ret = test_environment.call(['punch', '--action', 'mbuild'])

    assert not ret.stderr
    assert test_environment.get_file_content("README.md") == \
        "Version {}.{}.1.".format(system_year, system_month)
