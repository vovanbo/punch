import os
import re
import subprocess

import six

from punch.vcs.exceptions import (
    RepositorySystemError, RepositoryConfigurationError, RepositoryStatusError
)


class VCSRepo(object):
    def __init__(self, working_path, config_obj):
        self.working_path = working_path
        self.config_obj = config_obj

        self._check_config()
        self._set_command()
        self._check_system()

    def _check_config(self):
        pass

    def _set_command(self):
        self.commands = [None]
        self.command = None

    def _check_system(self):
        null_commands = self.commands + ["--help"]

        if six.PY2:
            not_found_exception = IOError
        else:
            not_found_exception = FileNotFoundError

        try:
            if six.PY2:
                subprocess.check_output(null_commands)
            else:
                subprocess.check_call(null_commands, stdout=subprocess.DEVNULL)

        except not_found_exception:
            raise RepositorySystemError("Cannot run {}".format(self.command))
        except subprocess.CalledProcessError:
            raise RepositorySystemError(
                "Error running {}".format(self.command))

    def _run(self, command_line, error_message=None):
        p = subprocess.Popen(
            command_line,
            cwd=self.working_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()

        if p.returncode != 0:
            if error_message is not None:
                raise RepositorySystemError(error_message.format(stderr))
            else:
                error_text = "An error occurred executing " \
                             "'{}': {}\nProcess output was: {}"
                error_message = error_text.format(
                    " ".join(command_line),
                    stderr.decode('utf8'), stdout.decode('utf8')
                )
                raise RepositorySystemError(error_message)

        return stdout.decode('utf8')

    def pre_start_release(self):
        raise NotImplementedError()

    def start_release(self):
        raise NotImplementedError()

    def finish_release(self):
        raise NotImplementedError()

    def post_finish_release(self):
        raise NotImplementedError()


class GitRepo(VCSRepo):
    def __init__(self, working_path, config_obj):
        if six.PY2:
            super(GitRepo, self).__init__(working_path, config_obj)
        else:
            super().__init__(working_path, config_obj)

        self.make_release_branch = self.config_obj.options.get(
            'make_release_branch',
            True
        )

    def _check_config(self):
        # Tag names cannot contain spaces
        tag = self.config_obj.options.get('tag', '')
        if ' ' in tag:
            raise RepositoryConfigurationError(
                "You specified \"'tag': {}\". "
                "Tag names cannot contain spaces".format(tag)
            )

    def _check_system(self):
        if six.PY2:
            super(GitRepo, self)._check_system()
        else:
            super()._check_system()

        if not os.path.exists(os.path.join(self.working_path, '.git')):
            raise RepositorySystemError(
                "The current directory {} "
                "is not a Git repository".format(self.working_path)
            )

    def _set_command(self):
        self.commands = ['git']
        self.command = 'git'

    def get_current_branch(self):
        stdout = self._run([self.command, "rev-parse", "--abbrev-ref", "HEAD"])

        branch = stdout.replace("\n", "")

        return branch

    def get_tags(self):
        return self._run([self.command, "tag"])

    def get_branches(self):
        return self._run([self.command, "branch"])

    def pre_start_release(self):
        output = self._run([self.command, "status"])
        if "Changes to be committed:" in output:
            raise RepositoryStatusError(
                "Cannot checkout master while repository "
                "contains uncommitted changes"
            )

        self._run([self.command, "checkout", "master"])

        branch = self.get_current_branch()

        if branch != "master":
            raise RepositoryStatusError(
                "Current branch shall be master but is {}".format(branch))

    def start_release(self):
        if self.make_release_branch:
            self._run([
                self.command, "checkout",
                "-b", self.config_obj.options['new_version']
            ])

    def finish_release(self):
        branch = self.get_current_branch()

        self._run([self.command, "add", "."])

        output = self._run([self.command, "status"])

        if ("nothing to commit, working directory clean" in output or
                "nothing to commit, working tree clean" in output) and \
                self.make_release_branch:
            self._run([self.command, "checkout", "master"])
            self._run([self.command, "branch", "-d", branch])
            return

        command_line = [self.command, "commit"]
        command_line.extend(["-m", self.config_obj.commit_message])

        self._run(command_line)

        if self.make_release_branch:
            self._run([self.command, "checkout", "master"])
            self._run([self.command, "merge", branch])
            self._run([self.command, "branch", "-d", branch])

        try:
            tag_value = self.config_obj.options['tag']
        except KeyError:
            tag_value = self.config_obj.options['new_version']

        if self.config_obj.options.get('annotate_tags', False):
            annotation_message = self.config_obj.options.get(
                'annotation_message', "Version {{ new_version }}")
            self._run([
                self.command, "tag",
                "-a", tag_value,
                "-m", annotation_message
            ])
        else:
            self._run([self.command, "tag", tag_value])

    def post_finish_release(self):
        pass

    def tag(self, tag_name):
        self._run([self.command, "tag", tag_name])


class GitFlowRepo(GitRepo):
    def __init__(self, working_path, config_obj):
        if six.PY2:
            super(GitFlowRepo, self).__init__(working_path, config_obj)
        else:
            super().__init__(working_path, config_obj)

    def _set_command(self):
        self.commands = ['git', 'flow']
        self.command = 'git'

    def _check_system(self):
        # git flow -h returns 1 so the call fails

        p = subprocess.Popen(
            self.commands,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = p.communicate()

        if "git flow <subcommand>" not in stdout.decode('utf8'):
            raise RepositorySystemError("Cannot run {}".format(self.commands))

        if not os.path.exists(os.path.join(self.working_path, '.git')):
            raise RepositorySystemError(
                "The current directory {} is not a Git repository".format(
                    self.working_path))

    def pre_start_release(self):
        output = self._run([self.command, "status"])
        if "Changes to be committed:" in output:
            raise RepositoryStatusError(
                "Cannot checkout master while repository "
                "contains uncommitted changes"
            )

        self._run([self.command, "checkout", "develop"])

        branch = self.get_current_branch()

        if branch != "develop":
            raise RepositoryStatusError(
                "Current branch shall be master but is {}".format(branch))

    def start_release(self):
        self._run(
            self.commands + [
                "release", "start",
                self.config_obj.options['new_version']
            ])

    def finish_release(self):
        branch = self.get_current_branch()

        self._run([self.command, "add", "."])

        output = self._run([self.command, "status"])
        if "nothing to commit, working directory clean" in output or \
                "nothing to commit, working tree clean" in output:
            self._run([self.command, "checkout", "develop"])
            self._run([self.command, "branch", "-d", branch])
            return

        message = ["-m", self.config_obj.commit_message]

        command_line = [self.command, "commit"]
        command_line.extend(message)

        self._run(command_line)

        self._run(
            self.commands + [
                "release", "finish",
                "-m", branch,
                self.config_obj.options['new_version']
            ])

    def post_finish_release(self):
        pass


class HgRepo(VCSRepo):
    DEFAULT_BRANCH = 'default'

    def __init__(self, working_path, config_obj):
        if six.PY2:
            super(HgRepo, self).__init__(working_path, config_obj)
        else:
            super().__init__(working_path, config_obj)

        self.branch = self.config_obj.options.get('branch', 'default')
        self._recorded_branch = None

    def get_current_branch(self):
        stdout = self._run([self.command, "branch"])

        branch = stdout.replace("\n", "")

        return branch

    def get_branches(self):
        stdout = self._run([self.command, "branches"])
        return {self._parse_branch_line(l) for l in stdout.splitlines()}

    def get_tags(self):
        tags_str = self._run([self.command, "tags"])
        tags = map(
            lambda l: l.rsplit(" ", 1)[0].strip(),
            tags_str.splitlines()
        )
        return "\n".join(tags)

    def get_summary(self):
        output = self._run([self.command, "summary"])
        keys = {"branch", "commit", "update"}
        summary = {}
        for l in output.splitlines():
            try:
                k, body = l.split(": ", 1)
                if k in keys:
                    summary[k] = body
            except ValueError:
                pass

        return summary

    def pre_start_release(self):
        if not self._is_clean():
            raise RepositoryStatusError(
                "Cannot update default while repository "
                "contains uncommitted changes")
        self._recorded_branch = self.get_current_branch()

        self._change_branch(self.branch)

        branch = self.get_current_branch()

        if branch != self.branch:
            raise RepositoryStatusError(
                "Current branch shall be {} "
                "but is {}".format(self.branch, branch)
            )

    def start_release(self):
        pass

    def finish_release(self):
        self.get_current_branch()
        try:
            if self._is_clean():
                return
            command_line = [self.command, "commit"]
            command_line.extend(["-m", self.config_obj.commit_message])
            self._run(command_line)
            tag = self._configured_tag()
            self.tag(tag)
        finally:
            self._recover_branch()

    def tag(self, tag):
        self._run([self.command, "tag", tag])

    def _recover_branch(self):
        if self._recorded_branch is not None:
            self._change_branch(self._recorded_branch)
            self._recorded_branch = None

    def _change_branch(self, branch):
        self._run([self.command, "update", branch])

    def _check_config(self):
        # Tag names cannot contain spaces
        tag = self.config_obj.options.get('tag', '')
        if ' ' in tag:
            raise RepositoryConfigurationError(
                "You specified \"'tag': {}\". "
                "Tag names cannot contain spaces".format(tag)
            )
        if re.match("^\d+$", tag):
            raise RepositoryConfigurationError(
                "You specified \"'tag': {}\". "
                "Tag names cannot be just digits".format(tag)
            )

    def _check_system(self):
        if six.PY2:
            super(HgRepo, self)._check_system()
        else:
            super()._check_system()

        if not os.path.exists(os.path.join(self.working_path, '.hg')):
            raise RepositorySystemError(
                "The current directory {} "
                "is not a Hg repository".format(self.working_path)
            )

    def _set_command(self):
        self.commands = ['hg']
        self.command = 'hg'

    def _is_clean(self):
        return self.get_summary()["commit"].endswith("(clean)")

    @classmethod
    def _parse_branch_line(cls, line):
        return re.match("(?P<tag>.+)\s+\d+:.+$", line).group("tag").strip()

    def _configured_tag(self):
        try:
            return self.config_obj.options['tag']
        except KeyError:
            return self.config_obj.options['new_version']
