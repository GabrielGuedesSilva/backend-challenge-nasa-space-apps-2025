from typing import List

from sqlalchemy import Column
from sqlalchemy.sql import operators

pagination_fields = ('limit', 'offset')
OPERATORS = {
    'ne': operators.ne,
    'lt': operators.lt,
    'lte': operators.le,
    'gt': operators.gt,
    'gte': operators.ge,
    'in': operators.in_op,
}


class Query:
    def __init__(self, query_params: dict = None):
        self.filters: dict = {
            key: value
            for key, value in query_params.items()
            if key not in pagination_fields
        }
        self.limit = (
            int(query_params['limit']) if 'limit' in query_params else None
        )
        self.offset = int(query_params.get('offset', 0))

    def build_filters(self, model_cls) -> List:
        expressions = []

        for field_name, value in self.filters.items():
            column: Column = getattr(model_cls, field_name, None)
            if column is None:
                continue

            if isinstance(value, dict):
                for op_key, op_value in value.items():
                    operator_fn = OPERATORS.get(op_key)
                    if operator_fn is not None:
                        expressions.append(operator_fn(column, op_value))
            else:
                expressions.append(column == value)

        return expressions

    def __str__(self):
        return (
            f'(filters={self.filters}, limit={self.limit}, '
            'offset={self.offset})'
        )
