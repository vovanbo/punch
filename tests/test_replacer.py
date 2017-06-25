import six

import pytest
import io

from punch.replacer import Replacer
from punch.version import Version
from punch.version_part import IntegerVersionPart


@pytest.fixture
def current_version():
    v = Version()
    v.add_part(IntegerVersionPart(name='major', value=1))
    v.add_part(IntegerVersionPart(name='minor', value=0))
    v.add_part(IntegerVersionPart(name='patch', value=0))
    return v


@pytest.fixture
def new_patch_version():
    v = Version()
    v.add_part(IntegerVersionPart(name='major', value=1))
    v.add_part(IntegerVersionPart(name='minor', value=0))
    v.add_part(IntegerVersionPart(name='patch', value=1))
    return v


@pytest.fixture
def new_minor_version():
    v = Version()
    v.add_part(IntegerVersionPart(name='major', value=1))
    v.add_part(IntegerVersionPart(name='minor', value=1))
    v.add_part(IntegerVersionPart(name='patch', value=0))
    return v


def file_like(file_content):
    if six.PY2:
        return io.StringIO(unicode(file_content)) # NOQA
    else:
        return io.StringIO(file_content)


def test_replace_content_without_config():
    with pytest.raises(TypeError):
        Replacer()


def test_replace_content(current_version, new_patch_version):
    file_content = """# Just a comment
    __version__ = "1.0.0"
    """

    updated_file_content = """# Just a comment
    __version__ = "1.0.1"
    """

    serializer = "__version__ = \"{{major}}.{{minor}}.{{patch}}\""
    replacer = Replacer(serializer)

    new_file_content = replacer(file_content, current_version,
                                new_patch_version)

    assert new_file_content == updated_file_content


def test_get_versions(current_version, new_patch_version):
    serializer = "__version__ = \"{{major}}.{{minor}}.{{patch}}\""
    replacer = Replacer(serializer)

    list_of_versions = replacer.run_all_serializers(current_version,
                                                    new_patch_version)

    assert list_of_versions == [
        ("__version__ = \"1.0.0\"", "__version__ = \"1.0.1\"")
    ]


def test_get_versions_with_multiple_serializers(current_version,
                                                new_patch_version):
    serializers = [
        "__version__ = \"{{major}}.{{minor}}.{{patch}}\"",
        "__api_abi__ = \"{{major}}.{{minor}}\""
    ]
    replacer = Replacer(serializers)

    list_of_versions = replacer.run_all_serializers(current_version,
                                                    new_patch_version)

    assert list_of_versions == [
        ("__version__ = \"1.0.0\"", "__version__ = \"1.0.1\""),
        ("__api_abi__ = \"1.0\"", "__api_abi__ = \"1.0\"")
    ]


def test_get_main_version_change_with_multiple_serializers(current_version,
                                                           new_patch_version):
    serializers = [
        "__version__ = \"{{major}}.{{minor}}.{{patch}}\"",
        "__api_abi__ = \"{{major}}.{{minor}}\""
    ]
    replacer = Replacer(serializers)

    current, new = replacer.run_main_serializer(current_version,
                                                new_patch_version)

    assert current, new == (
        "__version__ = \"1.0.0\"", "__version__ = \"1.0.1\""
    )


def test_replace_content_with_multiple_serializers(current_version,
                                                   new_patch_version):
    file_content = """# Just a comment
    __version__ = "1.0.0"
    __api_abi__ = "1.0"
    """

    updated_file_content = """# Just a comment
    __version__ = "1.0.1"
    __api_abi__ = "1.0"
    """

    serializers = [
        "__version__ = \"{{major}}.{{minor}}.{{patch}}\"",
        "__api_abi__ = \"{{major}}.{{minor}}\""
    ]

    replacer = Replacer(serializers)

    new_file_content = replacer(file_content, current_version,
                                new_patch_version)

    assert new_file_content == updated_file_content


def test_replace_content_without_using_all_parts(current_version,
                                                 new_minor_version):
    file_content = """# Just a comment
    __version__ = "1.0"
    """

    updated_file_content = """# Just a comment
    __version__ = "1.1"
    """

    serializer = "__version__ = \"{{major}}.{{minor}}\""
    replacer = Replacer(serializer)

    new_file_content = replacer(file_content, current_version,
                                new_minor_version)

    assert new_file_content == updated_file_content
