from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pandas as pd

from services.validator import LoadSpec, is_empty


def transform_dataframe(dataframe: pd.DataFrame, spec: LoadSpec) -> pd.DataFrame:
    transformed = dataframe.loc[:, spec.final_columns].copy()

    for column in transformed.columns:
        transformed[column] = transformed[column].map(normalize_value)

    return transformed


def normalize_value(value: object) -> str:
    if is_empty(value):
        return "NA"

    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()

    if isinstance(value, datetime):
        if value.time() == datetime.min.time():
            return value.date().isoformat()
        return value.isoformat(sep=" ", timespec="seconds")

    if isinstance(value, date):
        return value.isoformat()

    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)

    if isinstance(value, Decimal):
        return format(value, "f")

    text = str(value).replace("\xa0", " ").strip()
    return text if text else "NA"
