# -*- coding: utf-8 -*-
import pytest

from punch.version import Version
from punch.version_part import IntegerVersionPart, ValueListVersionPart


def clean_previous_imports():
    import sys

    for i in ['punch_config', 'punch_version']:
        if i in sys.modules:
            sys.modules.pop(i)


@pytest.fixture
def version_mmp():
    v = Version()
    v.create_part('major', value=4)
    v.create_part('minor', value=3)
    v.create_part('patch', value=1)
    return v


@pytest.fixture
def version_mmpb():
    v = Version()
    v.create_part('major', value=4)
    v.create_part('minor', value=3)
    v.create_part('patch', value=1)
    v.create_part('build', start_value=1, value=5)
    return v


def test_version_default_part_is_integer():
    v = Version()
    v.create_part('major', value=4)
    assert isinstance(v.get_part('major'), IntegerVersionPart)


def test_version_add_parts():
    v = Version()
    part_major = IntegerVersionPart(name='major', value=4)
    part_minor = IntegerVersionPart(name='minor', value=3)
    v.add_part(part_major)
    v.add_part(part_minor)

    assert v.get_part('major').value == 4
    assert v.get_part('minor').value == 3
    assert tuple(v.keys()) == ('major', 'minor')


def test_version_may_specify_part_class():
    v = Version()
    v.create_part(name='major', cls=ValueListVersionPart,
                  allowed_values=[0, 2, 4, 6, 8], value=4)
    assert isinstance(v.get_part('major'), ValueListVersionPart)
    assert v.get_part('major').value == '4'
    assert v.get_part('major').values == ['0', '2', '4', '6', '8']


def test_version_can_add_parts(version_mmp):
    assert version_mmp.get_part('major').value == 4


def test_version_increment_last_part(version_mmp):
    version_mmp.inc('patch')
    assert version_mmp.get_part('patch').value == 2


def test_version_increment_middle_part(version_mmp):
    version_mmp.inc('minor')
    assert version_mmp.get_part('minor').value == 4
    assert version_mmp.get_part('patch').value == 0


def test_version_increment_first_part(version_mmp):
    version_mmp.inc('major')
    assert version_mmp.get_part('major').value == 5
    assert version_mmp.get_part('minor').value == 0
    assert version_mmp.get_part('patch').value == 0


def test_version_set_last_part(version_mmp):
    version_mmp.set({
        'patch': 8
    })
    assert version_mmp.get_part('major').value == 4
    assert version_mmp.get_part('minor').value == 3
    assert version_mmp.get_part('patch').value == 8


def test_version_set_middle_part(version_mmp):
    version_mmp.set({
        'minor': 12
    })
    assert version_mmp.get_part('major').value == 4
    assert version_mmp.get_part('minor').value == 12
    assert version_mmp.get_part('patch').value == 1


def test_version_set_first_part(version_mmp):
    version_mmp.set({
        'major': 9
    })
    assert version_mmp.get_part('major').value == 9
    assert version_mmp.get_part('minor').value == 3
    assert version_mmp.get_part('patch').value == 1


def test_version_set_and_reset_first_part(version_mmp):
    version_mmp.set_and_reset('major', 9)
    assert version_mmp.get_part('major').value == 9
    assert version_mmp.get_part('minor').value == 0
    assert version_mmp.get_part('patch').value == 0


def test_version_increment_part_with_custom_start_value(version_mmpb):
    version_mmpb.inc('major')
    assert version_mmpb.get_part('major').value == 5
    assert version_mmpb.get_part('minor').value == 0
    assert version_mmpb.get_part('patch').value == 0
    assert version_mmpb.get_part('build').value == 1


def test_version_copy(version_mmp):
    new_version = version_mmp.copy()
    new_version.inc('major')
    assert new_version['major'].value == 5
    assert new_version['minor'].value == 0
    assert new_version['patch'].value == 0


def test_version_compare_equal(version_mmp):
    new_version = version_mmp.copy()
    assert new_version == version_mmp


def test_version_compare_differ(version_mmp):
    new_version = version_mmp.copy()
    new_version.inc('major')
    assert new_version != version_mmp


def test_version_as_list(version_mmp):
    assert list(version_mmp.simplify()) == [('major', 4),
                                            ('minor', 3),
                                            ('patch', 1)]


def test_version_keys_and_values(version_mmp):
    assert tuple(version_mmp.keys()) == ('major', 'minor', 'patch')
    assert [i.value for i in version_mmp.values()] == [4, 3, 1]


def test_version_keys_keep_indertion_order(version_mmp):
    minor = version_mmp.pop('minor')
    version_mmp.add_part(minor)
    assert list(version_mmp.simplify()) == [('major', 4),
                                            ('patch', 1),
                                            ('minor', 3)]


def test_version_as_dict(version_mmp):
    expected_dict = {
        'major': 4,
        'minor': 3,
        'patch': 1
    }

    assert dict(version_mmp.simplify()) == expected_dict
