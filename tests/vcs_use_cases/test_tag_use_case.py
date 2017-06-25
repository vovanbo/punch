import mock

from punch.vcs.use_cases import VCSTagUseCase


def test_pre_tag():
    repo = mock.Mock()
    use_case = VCSTagUseCase(repo)

    use_case.tag("just_a_tag")

    assert repo.tag.called_with("just_a_tag")
