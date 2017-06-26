#!/usr/bin/env python

import argparse
import json
import os
import sys
from collections import OrderedDict, MutableMapping
from datetime import datetime

import punch
from punch.config import PunchConfig
from punch.defaults import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE
from punch.file_updater import FileUpdater
from punch.helpers import import_file
from punch.replacer import Replacer
from punch.vcs.configuration import VCSConfiguration
from punch.vcs.exceptions import RepositorySystemError
from punch.vcs.repositories import GitRepo, GitFlowRepo, HgRepo
from punch.vcs.use_cases import VCSReleaseUseCase

VCS_REPO_MAP = {
    'git': GitRepo,
    'git-flow': GitFlowRepo,
    'hg': HgRepo
}


def fatal_error(message, exception=None):
    print(message)
    if exception is not None:
        print('Exception {}: {}'.format(exception.__class__.__name__,
                                        str(exception)))
    sys.exit(1)


def show_version_parts(version):
    print(json.dumps(dict(version.simplify())))


def show_version_updates(version_changes):
    for current, new in version_changes:
        print('  * {} -> {}'.format(current, new))


def is_migration_required(*files):
    return all([os.path.exists(f) for f in files])


def migrate(args):
    config_module = import_file('punch_config', args.old_config_file)
    print('Imported config file: {}'.format(args.old_config_file))
    version_module = import_file('punch_version',
                                 args.old_version_file)
    print('Imported version file: {}'.format(args.old_version_file))
    new_config = OrderedDict()
    new_config['format'] = 1
    new_config['globals'] = config_module.GLOBALS
    new_config['files'] = config_module.FILES
    new_config['version'] = OrderedDict()
    new_config['version']['variables'] = config_module.VERSION
    variables = []
    for variable in new_config['version']['variables']:
        if isinstance(variable, MutableMapping):
            variables.append(variable['name'])
        else:
            variables.append(variable)
    new_config['version']['values'] = []
    for variable in variables:
        new_config['version']['values'].append(
            str(getattr(version_module, variable))
        )
    if getattr(config_module, 'VCS', None):
        new_config['vcs'] = config_module.VCS
    if getattr(config_module, 'ACTIONS', None):
        new_config['actions'] = config_module.ACTIONS

    if args.simulate:
        print('\nThese files will be removed:')
        for file_to_remove in (args.old_config_file,
                               args.old_version_file):
            print('  * {}'.format(file_to_remove))
        print('\nFile "{}" will be created '
              'with the following content:'.format(args.config_file))
        print(json.dumps(new_config, indent=4))
    else:
        print('\nMigration is started.\n')
        print('Create file "{}"'.format(args.config_file))
        with open(args.config_file, mode='w') as f:
            json.dump(new_config, f)
        if not os.path.exists(args.config_file):
            fatal_error('Config file "{}" creation '
                        'is failed.'.format(args.config_file))
        print('Remove files:')
        for file_to_remove in (args.old_config_file,
                               args.old_version_file):
            os.remove(file_to_remove)
            if os.path.exists(file_to_remove):
                fatal_error('File "{}" removing '
                            'is failed.'.format(file_to_remove))
            print('  * {}'.format(file_to_remove))
        print('\nMigration is successful!')


def main():
    parser = argparse.ArgumentParser(
        description='Manages file content with versions.'
    )
    parser.add_argument('-c', '--config-file', action='store',
                        help='Config file', default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-p', '--part', action='store')
    parser.add_argument('--set-part', action='store')
    parser.add_argument('-a', '--action', action='store')
    parser.add_argument('--reset-on-set', action='store_true')
    parser.add_argument('--verbose', action='store_true',
                        help="Be verbose")
    parser.add_argument('--version', action='store_true',
                        help='Print the Punch version and project information')
    parser.add_argument(
        '--init',
        action='store_true',
        help='Writes default initialization files '
             '(does not overwrite existing ones)'
    )
    parser.add_argument(
        '-s',
        '--simulate',
        action='store_true',
        help='Simulates the version increment and prints a summary '
             'of the relevant data'
    )
    parser.add_argument(
        '--migrate',
        action='store_true',
        help='Run migration from deprecated punch '
             'configuration and version files to punch.json. Can be simulated.'
    )
    parser.add_argument('--old-config-file', action='store',
                        help="Used in migration. Pass it if you used "
                             "custom config file, "
                             "different than 'punch_config.py'.",
                        default='punch_config.py')
    parser.add_argument('--old-version-file', action='store',
                        help="Used in migration. Pass it if you used "
                             "custom version file, "
                             "different than 'punch_version.py'.",
                        default='punch_version.py')

    args = parser.parse_args()

    # These are here just to avoid "can be not defined" messages by linters
    config = None
    repo = None

    if args.version is True:
        print('Punch version {}'.format(punch.__version__))
        print('Copyright (C) 2016-{:%Y} '
              'Leonardo Giordani'.format(datetime.now()))
        print('This is free software, see the LICENSE file.')
        print('Source: https://github.com/lgiordani/punch')
        print('Documentation: http://punch.readthedocs.io/en/latest/')
        sys.exit(0)

    if args.migrate is True:
        if not is_migration_required(args.old_config_file,
                                     args.old_version_file):
            print('Migration is not required.')
        else:
            migrate(args)
        sys.exit(0)

    if args.init is True:
        if is_migration_required(args.old_config_file, args.old_version_file):
            fatal_error('WARNING!\n'
                        'Deprecated configuration and version files '
                        'is detected.\n'
                        'Migration to new version of punch is required.\n'
                        'To migrate run the following command:\n'
                        'punch -c {} --migrate\n'.format(args.config_file))

        if not os.path.exists(args.config_file):
            with open(args.config_file, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
            print('* Created file "{}" with content:'.format(args.config_file))
            print(json.dumps(DEFAULT_CONFIG, indent=4))
        else:
            print('File "{}" already exists. '
                  'Initialization is not required.'.format(args.config_file))
        sys.exit(0)

    if not any([args.part, args.set_part, args.action]):
        fatal_error('You must specify one of --part, --set-part, or --action')

    if args.set_part and args.reset_on_set:
        set_parts = args.set_part.split(',')
        if len(set_parts) > 1:
            fatal_error('If you specify --reset-on-set you may set '
                        'only one value')

    if args.verbose:
        print('## Punch version {}'.format(punch.__version__))

    try:
        config = PunchConfig(args.config_file)
    except Exception as exc:
        fatal_error(
            'An error occurred while reading the configuration file.',
            exc
        )

    if not args.simulate and not config.files:
        fatal_error("You didn't configure any file")

    new_version = config.version.copy()

    if args.action:
        action = config.actions[args.action]
        new_version = action.process_version(new_version)
    else:
        if args.part:
            new_version.inc(args.part)

        if args.set_part:
            if args.reset_on_set:
                part, value = args.set_part.split('=')
                new_version.set_and_reset(part, value)
            else:
                set_dict = dict(i.split('=') for i in args.set_part.split(','))
                new_version.set(set_dict)

    global_replacer = Replacer(config.globals['serializer'])
    current_version_string, new_version_string = \
        global_replacer.run_main_serializer(config.version, new_version)

    if config.vcs is not None:
        special_variables = {
            'current_version': current_version_string,
            'new_version': new_version_string
        }

        vcs_configuration = VCSConfiguration.from_dict(
            config.vcs,
            config.globals,
            special_variables
        )
    else:
        vcs_configuration = None

    if args.simulate:
        print('* Current version')
        show_version_parts(config.version)

        print('\n* New version')
        show_version_parts(new_version)

        changes = global_replacer.run_all_serializers(config.version,
                                                      new_version)

        print('\n* Global version updates')
        show_version_updates(changes)

        if config.files:
            print('\nConfigured files')
            for file_configuration in config.files:
                updater = FileUpdater(file_configuration)
                print('* {}: '.format(file_configuration.path))
                changes = updater.get_summary(config.version, new_version)
                show_version_updates(changes)

        if vcs_configuration is not None:
            print('\n* Version control configuration')
            print('Name:', vcs_configuration.name)
            print('Commit message:', vcs_configuration.commit_message)
            print('Options:', vcs_configuration.options)

    else:
        if vcs_configuration is not None:
            repo_class = VCS_REPO_MAP.get(vcs_configuration.name)
            if repo_class is None:
                fatal_error(
                    'The requested version control system "{}" '
                    'is not supported.'.format(vcs_configuration.name)
                )

            try:
                repo = repo_class(os.getcwd(), vcs_configuration)
            except RepositorySystemError as exc:
                fatal_error(
                    'An error occurred while initializing '
                    'the version control repository',
                    exc
                )
        else:
            repo = None

        if vcs_configuration is not None:
            # TODO: Create a fake UseCase to allow running this
            # without a repo and outside this nasty if
            uc = VCSReleaseUseCase(repo)
            uc.pre_start_release()
            uc.start_release()

        for file_configuration in config.files:
            if args.verbose:
                print('* Updating file {}'.format(file_configuration.path))
            updater = FileUpdater(file_configuration)
            updater(config.version, new_version)

        config.dump(version=new_version, target=args.config_file,
                    verbose=args.verbose)

        if vcs_configuration is not None:
            uc.finish_release()
            uc.post_finish_release()
