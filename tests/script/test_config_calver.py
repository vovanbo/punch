import json
import subprocess
import pytest

pytestmark = pytest.mark.slow

config_file_content = json.dumps({
    'format': 1,
    'globals': {
        'serializer': '{{major}}.{{minor}}',
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
                'name': 'major',
                'type': 'date',
                'fmt': 'YYYY'
            },
            {
                'name': 'minor',
                'type': 'date',
                'fmt': 'MM'
            }
        ],
        'values': ['2016', '4']
    }
})


def test_update_major(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 2016.4.")
    test_environment.ensure_file_is_present("punch.json", config_file_content)

    system_year = subprocess.check_output(['date', '+%Y'])
    system_year = system_year.decode('utf8').replace('\n', '')

    system_month = subprocess.check_output(['date', '+%m'])
    system_month = system_month.decode('utf8').\
        replace('\n', '').replace('0', '')

    test_environment.call(["punch", "--part", "major"])

    assert test_environment.get_file_content("README.md") == \
        "Version {}.{}.".format(system_year, system_month)


def test_update_minor(test_environment):
    test_environment.ensure_file_is_present("README.md", "Version 2016.4.")
    test_environment.ensure_file_is_present("punch.json", config_file_content)

    system_month = subprocess.check_output(['date', '+%m'])
    system_month = system_month.decode(
        'utf8').replace('\n', '').replace('0', '')

    test_environment.call(["punch", "--part", "minor"])

    assert test_environment.get_file_content("README.md") == \
        "Version 2016.{}.".format(system_month)
