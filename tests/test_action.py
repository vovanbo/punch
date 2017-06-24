# -*- coding: utf-8 -*-

import pytest

from punch.action import ConditionalResetAction
from punch.version import Version
from punch.version_part import DateVersionPart, IntegerVersionPart


def test_conditional_reset_init_with_no_field():
    with pytest.raises(TypeError):
        ConditionalResetAction()


def test_conditional_reset_init_field():
    a = ConditionalResetAction('a')
    assert a.field == 'a'


def test_conditional_reset_init_field_explicit():
    a = ConditionalResetAction(field='a')
    assert a.field == 'a'


def test_conditional_reset_init_accepts_update_fields():
    a = ConditionalResetAction(
        field='a', update_fields=['b', 'c'])
    assert a.field == 'a'
    assert a.update_fields == ['b', 'c']


def test_conditional_reset_process_version_checks_all_update_fields(mocker):
    mocker.patch('punch.version_part.DateVersionPart.inc')
    v = Version()
    part_year = DateVersionPart('year', 2016, '%Y')
    part_month = DateVersionPart('month', 1, '%m')
    part_build = IntegerVersionPart('build')
    v.add_part(part_year)
    v.add_part(part_month)
    v.add_part(part_build)

    a = ConditionalResetAction(
        field='build',
        update_fields=['year', 'month']
    )

    a.process_version(v)

    assert part_year.inc.called
    assert part_month.inc.called


def test_conditional_reset_process_version_calls_reset_on_field(mocker):
    mocker.patch('punch.version_part.IntegerVersionPart.reset')
    v = Version()
    part_year = DateVersionPart('year', fmt='%Y', value=2016)
    part_month = DateVersionPart('month', fmt='%m', value=1)
    part_build = IntegerVersionPart('build')
    v.add_part(part_year)
    v.add_part(part_month)
    v.add_part(part_build)

    a = ConditionalResetAction(
        field='build',
        update_fields=['year', 'month']
    )

    a.process_version(v)

    assert part_build.reset.called


def test_conditional_reset_process_version_calls_increment_on_field(mocker):
    mocker.patch('punch.version_part.IntegerVersionPart.inc')
    strftime = mocker.patch('punch.version_part.strftime')
    strftime.return_value = 2016
    v = Version()
    part_year = DateVersionPart('year', fmt='%Y', value=2016)
    part_build = IntegerVersionPart('build')
    v.add_part(part_year)
    v.add_part(part_build)

    a = ConditionalResetAction(
        field='build',
        update_fields=['year']
    )

    a.process_version(v)

    assert part_build.inc.called
