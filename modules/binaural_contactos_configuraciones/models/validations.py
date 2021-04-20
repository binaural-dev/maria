# -*- coding: utf-8 -*-

import re


def not_number(string):
    record = string
    pattern = "[0-9]*"
    for data in record:
        if re.match(pattern, data).group() != '':
            return False
    return True


def case_upper(string,field_name):
    if string:
        result = {
            'value': {
                field_name: str(string).strip().upper()
            }
        }
        return result


def not_text(string):
    if string.isdigit()!=True:
        return False
    return True


def not_negative(number):
    if number > 0:
        return True
    return False


def not_text_no_required(string):
    if string:
        if string.isdigit()!=True:
            return False
        return True
    return True


def clear_field(array_field):
    result = {'value': {}}
    if len(array_field) > 0:
        for field in array_field:
            result['value'][field] = None
    return result

