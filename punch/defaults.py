from collections import OrderedDict

DEFAULT_COMMIT_MESSAGE = 'Version updated from {{ current_version }} ' \
                         'to {{ new_version }}'
DEFAULT_CONFIG_FILE = 'punch.json'
DEFAULT_CONFIG = OrderedDict({
    'format': 1,
    'globals': {
        'serializer': '{{major}}.{{minor}}.{{patch}}',
    },
    'files': [],
    'version': {
        'variables': ['major', 'minor', 'patch'],
        'current': ['0', '1', '0']
    },
    'vcs': {
        'name': 'git',
        'commit_message': DEFAULT_COMMIT_MESSAGE,
    }
})
