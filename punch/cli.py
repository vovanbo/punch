#!/usr/bin/env python

import argparse
import json
import os
import sys
from datetime import datetime

import punch
from punch.action import Action
from punch.config import PunchConfig, ConfigurationVersionError
from punch.defaults import DEFAULT_CONFIG, DEFAULT_CONFIG_FILE
from punch.file_updater import FileUpdater
from punch.replacer import Replacer
from punch.vcs_configuration import VCSConfiguration
from punch.vcs_repositories.exceptions import RepositorySystemError
from punch.vcs_repositories.git_flow_repo import GitFlowRepo
from punch.vcs_repositories.git_repo import GitRepo
from punch.vcs_repositories.hg_repo import HgRepo
from punch.vcs_use_cases.release import VCSReleaseUseCase

VCS_REPO_MAP = {
    'git': GitRepo,
    'git-flow': GitFlowRepo,
    'hg': HgRepo
}


def fatal_error(message, exception=None):
    print(message)
    if exception is not None:
        print("Exception {}: {}".format(exception.__class__.__name__,
                                        str(exception)))
    sys.exit(1)


def show_version_parts(values):
    for p in values:
        print("{}={}".format(p.name, p.value))


def show_version_updates(version_changes):
    for current, new in version_changes:
        print("  * {} -> {}".format(current, new))


def main():
    parser = argparse.ArgumentParser(
        description="Manages file content with versions."
    )
    parser.add_argument('-c', '--config-file', action='store',
                        help="Config file", default=DEFAULT_CONFIG_FILE)
    parser.add_argument('-p', '--part', action='store')
    parser.add_argument('--set-part', action='store')
    parser.add_argument('-a', '--action', action='store')
    parser.add_argument('--reset-on-set', action='store_true')
    parser.add_argument('--verbose', action='store_true',
                        help="Be verbose")
    parser.add_argument('--version', action='store_true',
                        help="Print the Punch version and project information")
    parser.add_argument(
        '--init',
        action='store_true',
        help="Writes default initialization files "
             "(does not overwrite existing ones)"
    )
    parser.add_argument(
        '-s',
        '--simulate',
        action='store_true',
        help="Simulates the version increment and prints a summary "
             "of the relevant data"
    )

    args = parser.parse_args()

    # These are here just to avoid "can be not defined" messages by linters
    config = None
    repo = None

    if args.version is True:
        print("Punch version {}".format(punch.__version__))
        print("Copyright (C) 2016-{} "
              "Leonardo Giordani".format(datetime.now().strftime('%Y')))
        print("This is free software, see the LICENSE file.")
        print("Source: https://github.com/lgiordani/punch")
        print("Documentation: http://punch.readthedocs.io/en/latest/")
        sys.exit(0)

    if args.init is True:
        if not os.path.exists(args.config_file):
            with open(args.config_file, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        sys.exit(0)

    if not any([args.part, args.set_part, args.action]):
        fatal_error("You must specify one of --part, --set-part, or --action")

    if args.set_part and args.reset_on_set:
        set_parts = args.set_part.split(',')
        if len(set_parts) > 1:
            fatal_error("If you specify --reset-on-set you may set "
                        "only one value")

    if args.verbose:
        print("## Punch version {}".format(punch.__version__))

    try:
        config = PunchConfig(args.config_file)
    except (ConfigurationVersionError, ValueError) as exc:
        fatal_error(
            "An error occurred while reading the configuration file.",
            exc
        )

    if not args.simulate:
        if len(config.files) == 0:
            fatal_error("You didn't configure any file")

    new_version = config.version.copy()

    if args.action:
        action_dict = config.actions[args.action]
        action = Action.from_dict(action_dict)
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
        print("* Current version")
        show_version_parts(config.version.values)

        print("\n* New version")
        show_version_parts(new_version.values)

        changes = global_replacer.run_all_serializers(config.version,
                                                      new_version)

        print("\n* Global version updates")
        show_version_updates(changes)

        print("\nConfigured files")
        for file_configuration in config.files:
            updater = FileUpdater(file_configuration)
            print("* {}: ".format(file_configuration.path))
            changes = updater.get_summary(config.version, new_version)
            show_version_updates(changes)

        if vcs_configuration is not None:
            print("\nVersion control configuration")
            print("Name:", vcs_configuration.name)
            print("Commit message", vcs_configuration.commit_message)
            print("Options:", vcs_configuration.options)

    else:
        if vcs_configuration is not None:
            repo_class = VCS_REPO_MAP.get(vcs_configuration.name)
            if repo_class is None:
                fatal_error(
                    "The requested version control "
                    "system {} is not supported.".format(vcs_configuration.name)
                )

            try:
                repo = repo_class(os.getcwd(), vcs_configuration)
            except RepositorySystemError as exc:
                fatal_error(
                    "An error occurred while initializing "
                    "the version control repository",
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
                print("* Updating file {}".format(file_configuration.path))
            updater = FileUpdater(file_configuration)
            updater(config.version, new_version)

        config.dump(version=new_version, target=args.config_file,
                    verbose=args.verbose)

        if vcs_configuration is not None:
            uc.finish_release()
            uc.post_finish_release()
