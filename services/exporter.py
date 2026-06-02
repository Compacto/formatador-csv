from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from services.validator import LoadSpec


OUTPUT_DIR = Path("output")


def make_output_filename(spec: LoadSpec, domain: str | None = None) -> str:
    if "{domain}" not in spec.output_filename:
        return spec.output_filename

    return spec.output_filename.format(domain=sanitize_domain(domain))


def sanitize_domain(value: str | None) -> str:
    text = "" if value is None else str(value).strip().lower()
    text = re.sub(r"[^a-z0-9_-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-_")
    return text or "dominio"


def export_dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    csv_text = export_dataframe_to_csv_text(dataframe)
    return csv_text.encode("utf-8")


def export_dataframe_to_csv_text(dataframe: pd.DataFrame) -> str:
    rows = [list(dataframe.columns)]
    rows.extend(dataframe.astype(str).values.tolist())
    return "\n".join(_format_csv_row(row) for row in rows) + "\n"


def save_csv(data: bytes, filename: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / filename
    output_path.write_bytes(data)
    return output_path


def _format_csv_row(row: list[object]) -> str:
    return ",".join(_format_csv_field(value) for value in row)


def _format_csv_field(value: object) -> str:
    text = "" if value is None else str(value)
    if _needs_quotes(text):
        return '"' + text.replace('"', '""') + '"'
    return text


def _needs_quotes(text: str) -> bool:
    return (
        " " in text
        or "\t" in text
        or "," in text
        or "\n" in text
        or "\r" in text
        or bool(re.search(r"<[^>]+>", text))
        or '"' in text
    )
