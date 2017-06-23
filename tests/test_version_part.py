# -*- coding: utf-8 -*-

import pytest

from punch.version_part import (
    IntegerVersionPart, ValueListVersionPart, VersionPart,
    DateVersionPart, strftime
)


def test_integer_version_part_init_with_integer():
    vp = IntegerVersionPart('major', 4)
    assert vp.value == 4


def test_integer_version_part_init_with_string():
    vp = IntegerVersionPart('major', '4')
    assert vp.value == 4


def test_integer_version_part_init_with_none():
    vp = IntegerVersionPart('major', None)
    assert vp.value == 0


def test_integer_version_part_init_without_value():
    vp = IntegerVersionPart('major')
    assert vp.value == 0


def test_integer_version_part_init_with_start_value():
    vp = IntegerVersionPart('major', start_value=1)
    assert vp.value == 1
    vp.inc()
    vp.reset()
    assert vp.value == 1


def test_integer_version_part_increases():
    vp = IntegerVersionPart('major', 4)
    vp.inc()
    assert vp.value == 5


def test_integer_version_part_set():
    vp = IntegerVersionPart('major', 4)
    vp.set(9)
    assert vp.value == 9


def test_integer_version_part_reset():
    vp = IntegerVersionPart('major', 4)
    vp.reset()
    assert vp.value == 0


def test_integer_version_part_copy():
    vp = IntegerVersionPart('major', 4)
    nvp = vp.copy()
    vp.inc()

    assert nvp.value == 4


def test_integer_version_part_with_start_value_copy():
    vp = IntegerVersionPart('major', 4, start_value=1)
    nvp = vp.copy()

    assert nvp.start_value == 1


def test_valuelist_version_part_init_with_allowed_value():
    vp = ValueListVersionPart('major', 0, [0, 2, 4, 6, 8])
    assert vp.value == 0


def test_valuelist_version_part_init_with_not_allowed_value():
    with pytest.raises(ValueError):
        ValueListVersionPart('major', 1, [0, 2, 4, 6, 8])


def test_valuelist_version_part_init_with_none():
    vp = ValueListVersionPart('major', None, [0, 2, 4, 6, 8])
    assert vp.value == 0


def test_valuelist_version_part_increase():
    vp = ValueListVersionPart('major', 0, [0, 2, 4, 6, 8])
    vp.inc()
    assert vp.value == 2


def test_valuelist_version_part_set():
    vp = ValueListVersionPart('major', 0, [0, 2, 4, 6, 8])
    vp.set(8)
    assert vp.value == 8


def test_valuelist_version_part_increase_from_last():
    vp = ValueListVersionPart('major', 8, [0, 2, 4, 6, 8])
    vp.inc()
    assert vp.value == 0


def test_valuelist_version_part_increase_with_non_numerical_values():
    vp = ValueListVersionPart(
        'major', 0, [0, 'alpha', 'beta', 'rc1', 'rc2', 1]
    )
    vp.inc()
    assert vp.value == 'alpha'


def test_valuelist_version_part_set_with_non_numerical_values():
    vp = ValueListVersionPart(
        'major', 0, [0, 'alpha', 'beta', 'rc1', 'rc2', 1]
    )
    vp.set('rc1')
    assert vp.value == 'rc1'


def test_valuelist_version_part_reset():
    vp = ValueListVersionPart('major', 4, [0, 2, 4, 6, 8])
    vp.reset()
    assert vp.value == 0


def test_valuelist_version_part_copy():
    vp = ValueListVersionPart('major', 4, [0, 2, 4, 6, 8])
    nvp = vp.copy()
    vp.inc()
    vp.values.append(9)

    assert nvp.value == 4
    assert nvp.values == [0, 2, 4, 6, 8]


def test_get_integer_version_part_from_full_dict():
    input_dict = {
        'name': 'major',
        'value': 1,
        'type': 'integer'
    }

    vp = VersionPart.from_dict(input_dict)

    assert vp.name == 'major'
    assert vp.value == 1
    assert isinstance(vp, IntegerVersionPart)


def test_get_integer_version_part_from_partial_dict():
    input_dict = {
        'name': 'major',
        'value': 1,
    }

    vp = VersionPart.from_dict(input_dict)

    assert vp.name == 'major'
    assert vp.value == 1
    assert isinstance(vp, IntegerVersionPart)


def test_get_value_list_version_part_from_full_dict():
    input_dict = {
        'name': 'major',
        'value': 'alpha',
        'type': 'value_list',
        'allowed_values': ['alpha', 'beta', 'stable']
    }

    vp = VersionPart.from_dict(input_dict)

    assert vp.name == 'major'
    assert vp.value == 'alpha'
    assert isinstance(vp, ValueListVersionPart)
    assert vp.values == ['alpha', 'beta', 'stable']


def test_date_version_part_init_without_value(mocker):
    mock_strftime = mocker.patch('punch.version_part.strftime')
    mock_strftime.return_value = '2018'
    vp = DateVersionPart('major', value=None, fmt='%Y')
    mock_strftime.assert_called_with('%Y')
    assert vp.value == '2018'


def test_date_version_part_init_with_value(mocker):
    mock_strftime = mocker.patch('punch.version_part.strftime')
    mock_strftime.return_value = '2018'
    vp = DateVersionPart('major', value='2017', fmt='%Y')
    mock_strftime.assert_not_called()
    assert vp.value == '2017'


def test_date_version_part_reset(mocker):
    mock_strftime = mocker.patch('punch.version_part.strftime')
    vp = DateVersionPart('major', value='2017', fmt='%Y')
    assert vp.value == '2017'
    mock_strftime.return_value = '2018'
    vp.reset()
    mock_strftime.assert_called_with('%Y')
    assert vp.value == '2018'


def test_date_version_part_increases_just_resets(mocker):
    mock_strftime = mocker.patch('punch.version_part.strftime')
    vp = DateVersionPart('major', value='2017', fmt='%Y')
    assert vp.value == '2017'
    mock_strftime.return_value = '2018'
    vp.inc()
    mock_strftime.assert_called_with('%Y')
    assert vp.value == '2018'


def test_date_version_part_copy():
    vp = DateVersionPart('major', value='2017', fmt='%Y%m')
    nvp = vp.copy()

    assert nvp.fmt == '%Y%m'


def test_strftime_full_year(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    strftime('YYYY')
    mock_strftime.assert_called_with('%Y')


def test_strftime_short_year(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    strftime('YY')
    mock_strftime.assert_called_with('%y')


def test_strftime_short_year_is_not_padded(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    mock_strftime.return_value = '03'
    assert strftime('YY') == '3'


def test_strftime_short_month(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    strftime('MM')
    mock_strftime.assert_called_with('%m')


def test_strftime_short_month_is_not_padded(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    mock_strftime.return_value = '04'
    assert strftime('MM') == '4'


def test_strftime_zero_padded_short_month(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    strftime('0M')
    mock_strftime.assert_called_with('%m')


def test_strftime_zero_padded_short_month_is_padded(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    mock_strftime.return_value = '04'
    assert strftime('0M') == '04'


def test_strftime_short_day(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    strftime('DD')
    mock_strftime.assert_called_with('%d')


def test_strftime_short_day_is_not_padded(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    mock_strftime.return_value = '04'
    assert strftime('DD') == '4'


def test_strftime_zero_padded_short_day(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    strftime('0D')
    mock_strftime.assert_called_with('%d')


def test_strftime_zero_padded_short_day_is_padded(mocker):
    mock_strftime = mocker.patch('punch.version_part.format_current_time')
    mock_strftime.return_value = '04'
    assert strftime('0D') == '04'
