# -*- coding: utf-8 -*-

from aioli.exceptions import InternalError


async def serialize_columns(value):
    if not isinstance(value, list):
        raise InternalError(f'Unable to serialize columns: {value}')

    columns_raw = ' '.join(value)
    return f"Columns: {columns_raw}"
