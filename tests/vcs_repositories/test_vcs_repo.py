import pytest
import six
from punch.vcs_repositories import base as vr, exceptions as re

if six.PY2:
    import mock
else:
    from unittest import mock

pytestmark = pytest.mark.slow


def _test_set_command(self):
    self.commands = ['ls']
    self.command = 'ls'


def test_init_without_program_installed(temp_empty_dir):
    with mock.patch("subprocess.Popen") as mock_popen:
        if six.PY2:
            mock_popen.side_effect = IOError
        else:
            mock_popen.side_effect = FileNotFoundError

        with pytest.raises(re.RepositorySystemError):
            vr.VCSRepo._set_command = _test_set_command
            vr.VCSRepo(temp_empty_dir, mock.Mock())


def test_run_without_errors(temp_empty_dir):
    with mock.patch('subprocess.check_call'):
        vr.VCSRepo._set_command = _test_set_command
        repo = vr.VCSRepo(temp_empty_dir, mock.Mock())

    with mock.patch('subprocess.Popen') as mock_popen:
        mock_popen_obj = mock.Mock()
        mock_popen.return_value = mock_popen_obj
        mock_popen_obj.communicate.return_value = \
            ("stdout".encode("utf8"), "stderr".encode("utf8"))
        mock_popen_obj.returncode = 0

        assert repo._run([repo.command, "--help"]) == "stdout"


def test_run_with_errors(temp_empty_dir):
    with mock.patch('subprocess.check_call'):
        vr.VCSRepo._set_command = _test_set_command
        repo = vr.VCSRepo(temp_empty_dir, mock.Mock())

    with mock.patch('subprocess.Popen') as mock_popen:
        mock_popen_obj = mock.Mock()
        mock_popen.return_value = mock_popen_obj
        mock_popen_obj.communicate.return_value = \
            ("stdout".encode("utf8"), "stderr".encode("utf8"))
        mock_popen_obj.returncode = 1

        with pytest.raises(vr.RepositorySystemError) as exc:
            assert repo._run([repo.command, "--help"])

        assert str(exc.value) == \
            "An error occurred executing '{} --help':".format(repo.command) + \
            " stderr\nProcess output was: stdout"


def test_initialize_repo_with_global_configuration_object(
        mocker, temp_empty_dir):
    global_config = mocker.Mock()
    repo = vr.VCSRepo(temp_empty_dir, config_obj=global_config)
    assert repo.config_obj == global_config
