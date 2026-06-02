from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from html import unescape
from html.parser import HTMLParser
import re
import unicodedata
from typing import Literal

import pandas as pd


IssueSeverity = Literal["error", "warning"]


@dataclass(frozen=True)
class LoadSpec:
    label: str
    output_filename: str
    template_filename: str
    expected_columns: list[str]
    final_columns: list[str]
    html_columns: list[str]
    requires_domain: bool = False
    default_missing_columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class ValidationIssue:
    severity: IssueSeverity
    line: int | None
    field: str
    description: str


@dataclass(frozen=True)
class ValidationResult:
    dataframe: pd.DataFrame
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


LOAD_SPECS: dict[str, LoadSpec] = {
    "Overview - Dataset": LoadSpec(
        label="Overview - Dataset",
        output_filename="overview-dataset-{domain}.csv",
        template_filename="overview-dataset-dominio.xlsx",
        expected_columns=[
            "project",
            "dataset",
            "overview",
            "tipo de ação",
            "justificativa",
        ],
        final_columns=["project", "dataset", "overview"],
        html_columns=["overview"],
        requires_domain=True,
    ),
    "Overview - Table": LoadSpec(
        label="Overview - Table",
        output_filename="overview-table-{domain}.csv",
        template_filename="overview-table-dominio.xlsx",
        expected_columns=[
            "project",
            "dataset",
            "table",
            "overview",
            "tipo de ação",
            "justificativa",
        ],
        final_columns=["project", "dataset", "table", "overview"],
        html_columns=["overview"],
        requires_domain=True,
    ),
    "Aspect - Dataset": LoadSpec(
        label="Aspect - Dataset",
        output_filename="dataset-information.csv",
        template_filename="dataset-information.xlsx",
        expected_columns=[
            "project",
            "dataset",
            "dt_aprv_gov",
            "nm_own_stwd",
            "nm_cust",
            "nm_dom",
            "nm_cam",
            "fl_reg_apl",
            "nm_avl_risco",
            "nm_lgl_lgpd",
            "fl_ropa",
            "nm_class_inf",
            "fl_pii",
            "fl_sens",
            "fl_mask",
            "ct_qld_status",
            "ct_area_neg",
            "tipo de ação",
            "justificativa",
        ],
        final_columns=[
            "project",
            "dataset",
            "dt_aprv_gov",
            "nm_own_stwd",
            "nm_cust",
            "nm_dom",
            "nm_cam",
            "fl_reg_apl",
            "nm_avl_risco",
            "nm_lgl_lgpd",
            "fl_ropa",
            "nm_class_inf",
            "fl_pii",
            "fl_sens",
            "fl_mask",
            "ct_qld_status",
            "ct_area_neg",
        ],
        html_columns=[],
    ),
    "Aspect - Table/View": LoadSpec(
        label="Aspect - Table/View",
        output_filename="table-information.csv",
        template_filename="table-information.xlsx",
        expected_columns=[
            "project",
            "dataset",
            "table",
            "dt_aprv_gov",
            "nm_own_stwd",
            "nm_cust",
            "nm_dom",
            "nm_cam",
            "fl_reg_apl",
            "nm_lgl_lgpd",
            "nm_class_inf",
            "fl_pii",
            "fl_sens",
            "nm_retencao",
            "fl_mask",
            "ct_qld_status",
            "fl_apt_cons",
            "dt_inc",
            "ct_qld_selo",
            "ct_cons_exec",
            "fl_legado",
            "ct_prod_neg",
            "ct_area_neg",
            "ct_risco",
            "tipo de ação",
            "justificativa",
        ],
        final_columns=[
            "project",
            "dataset",
            "table",
            "dt_aprv_gov",
            "nm_own_stwd",
            "nm_cust",
            "nm_dom",
            "nm_cam",
            "fl_reg_apl",
            "nm_lgl_lgpd",
            "nm_class_inf",
            "fl_pii",
            "fl_sens",
            "nm_retencao",
            "fl_mask",
            "ct_qld_status",
            "fl_apt_cons",
            "dt_inc",
            "ct_qld_selo",
            "ct_cons_exec",
            "fl_legado",
            "ct_prod_neg",
            "ct_area_neg",
            "ct_risco",
        ],
        html_columns=[],
    ),
    "Aspect - Column": LoadSpec(
        label="Aspect - Column",
        output_filename="column-information.csv",
        template_filename="column-information.xlsx",
        expected_columns=[
            "project",
            "dataset",
            "table",
            "column",
            "fl_reg_apl",
            "fl_atr_pii",
            "nm_atr_pii",
            "fl_atr_sens",
            "fl_atr_mask",
            "fl_meta_conf",
            "tipo de ação",
            "justificativa",
        ],
        final_columns=[
            "project",
            "dataset",
            "table",
            "column",
            "fl_reg_apl",
            "fl_atr_pii",
            "nm_atr_pii",
            "fl_atr_sens",
            "fl_atr_mask",
            "fl_meta_conf",
        ],
        html_columns=[],
        default_missing_columns=("fl_meta_conf",),
    ),
    "Glossário": LoadSpec(
        label="Glossário",
        output_filename="glossary-insert.csv",
        template_filename="glossary-insert.xlsx",
        expected_columns=[
            "Categoria 1",
            "Categoria 2",
            "Categoria 3",
            "Termo",
            "Description",
            "Overview",
        ],
        final_columns=[
            "Categoria 1",
            "Categoria 2",
            "Categoria 3",
            "Termo",
            "Description",
            "Overview",
        ],
        html_columns=["Description", "Overview"],
    ),
}


def get_load_spec(label: str) -> LoadSpec:
    return LOAD_SPECS[label]


def read_excel_file(uploaded_file) -> pd.DataFrame:
    return pd.read_excel(uploaded_file, sheet_name=0, dtype=object, engine="openpyxl")


def validate_dataframe(raw_dataframe: pd.DataFrame, spec: LoadSpec) -> ValidationResult:
    dataframe = _drop_empty_rows(_drop_empty_unnamed_columns(raw_dataframe.copy()))
    dataframe, header_issues = _canonicalize_headers(dataframe, spec)
    dataframe = _add_default_missing_columns(dataframe, spec)

    errors = [issue for issue in header_issues if issue.severity == "error"]
    warnings = [issue for issue in header_issues if issue.severity == "warning"]

    if dataframe.empty:
        errors.append(
            ValidationIssue(
                severity="error",
                line=None,
                field="arquivo",
                description="A planilha não possui linhas de dados.",
            )
        )
        return ValidationResult(dataframe=dataframe, errors=errors, warnings=warnings)

    if errors:
        return ValidationResult(dataframe=dataframe, errors=errors, warnings=warnings)

    dataframe = dataframe.loc[:, spec.expected_columns]
    dataframe = _drop_rows_empty_in_columns(dataframe, spec.expected_columns)

    if dataframe.empty:
        errors.append(
            ValidationIssue(
                severity="error",
                line=None,
                field="arquivo",
                description="A planilha possui cabeçalho válido, mas nenhuma linha preenchida.",
            )
        )
        return ValidationResult(dataframe=dataframe, errors=errors, warnings=warnings)

    for row_index, row in dataframe.iterrows():
        excel_line = int(row_index) + 2
        for field in spec.final_columns:
            value = row[field]
            if field in spec.html_columns:
                html_error = validate_html_fragment(value)
                if html_error:
                    errors.append(
                        ValidationIssue(
                            severity="error",
                            line=excel_line,
                            field=field,
                            description=html_error,
                        )
                    )
                continue

            if is_empty(value):
                warnings.append(
                    ValidationIssue(
                        severity="warning",
                        line=excel_line,
                        field=field,
                        description=f"Campo {field} vazio; será substituído por NA.",
                    )
                )

    return ValidationResult(dataframe=dataframe, errors=errors, warnings=warnings)


def is_empty(value: object) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).replace("\xa0", " ").strip() == ""


def normalize_header(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\ufeff", "").strip()
    text = re.sub(r"\s+", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return text.casefold()


HEADER_ALIASES = {
    normalize_header("Justificativa da Solicitação"): "justificativa",
}


def validate_html_fragment(value: object) -> str | None:
    if is_empty(value):
        return "HTML vazio."

    text = str(value).strip()
    parser = _BalancedHTMLParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # pragma: no cover - HTMLParser is permissive, this is a guard rail.
        return f"HTML inválido: {exc}"

    if parser.errors:
        return "HTML inválido: " + "; ".join(parser.errors)

    if parser.open_tags:
        tag = parser.open_tags[-1]
        return f"HTML inválido: tag <{tag}> aberta e não fechada."

    visible_text = re.sub(r"<[^>]*>", "", text)
    visible_text = unescape(visible_text).replace("\xa0", " ").strip()
    if not visible_text:
        return "HTML sem texto visível."

    return None


def _canonicalize_headers(
    dataframe: pd.DataFrame, spec: LoadSpec
) -> tuple[pd.DataFrame, list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    expected_by_normalized = {
        normalize_header(column): column for column in spec.expected_columns
    }
    original_by_normalized: dict[str, str] = {}
    rename_map: dict[object, str] = {}

    for original_column in dataframe.columns:
        normalized = normalize_header(original_column)
        original_text = str(original_column).strip()
        canonical_column = HEADER_ALIASES.get(
            normalized, expected_by_normalized.get(normalized, original_text)
        )
        canonical_normalized = normalize_header(canonical_column)

        if canonical_normalized in original_by_normalized:
            issues.append(
                ValidationIssue(
                    severity="error",
                    line=None,
                    field=original_text,
                    description=(
                        "Cabeçalho duplicado. "
                        f"Também foi encontrado como {original_by_normalized[canonical_normalized]}."
                    ),
                )
            )
            continue

        original_by_normalized[canonical_normalized] = original_text
        rename_map[original_column] = canonical_column

    found_normalized = set(original_by_normalized)
    unexpected_columns = [
        original
        for normalized, original in original_by_normalized.items()
        if normalized not in expected_by_normalized
    ]

    for expected_column in spec.expected_columns:
        normalized = normalize_header(expected_column)
        if normalized in found_normalized:
            continue

        if expected_column in spec.default_missing_columns:
            issues.append(
                ValidationIssue(
                    severity="warning",
                    line=None,
                    field=expected_column,
                    description=(
                        f"Campo {expected_column} não encontrado no template; "
                        "será preenchido com NA."
                    ),
                )
            )
            continue

        similar = _guess_similar_header(normalized, original_by_normalized)
        description = f"Campo esperado '{expected_column}' não encontrado no cabeçalho."
        if similar:
            description += f" Campo encontrado semelhante: '{similar}'."

        issues.append(
            ValidationIssue(
                severity="error",
                line=None,
                field=expected_column,
                description=description,
            )
        )

    for unexpected_column in unexpected_columns:
        issues.append(
            ValidationIssue(
                severity="error",
                line=None,
                field=unexpected_column,
                description=(
                    f"Campo encontrado '{unexpected_column}' não faz parte do template "
                    f"{spec.label}."
                ),
            )
        )

    return dataframe.rename(columns=rename_map), issues


def _add_default_missing_columns(
    dataframe: pd.DataFrame, spec: LoadSpec
) -> pd.DataFrame:
    for column in spec.default_missing_columns:
        if column not in dataframe.columns:
            dataframe[column] = pd.NA

    return dataframe


def _guess_similar_header(
    expected_normalized: str, original_by_normalized: dict[str, str]
) -> str | None:
    matches = get_close_matches(
        expected_normalized, list(original_by_normalized), n=1, cutoff=0.65
    )
    if matches:
        return original_by_normalized[matches[0]]

    expected_tokens = set(re.split(r"[\W_]+", expected_normalized)) - {""}
    for normalized, original in original_by_normalized.items():
        found_tokens = set(re.split(r"[\W_]+", normalized)) - {""}
        if expected_tokens and expected_tokens & found_tokens:
            return original

    return None


def _drop_empty_unnamed_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    columns_to_drop = []
    for column in dataframe.columns:
        column_name = str(column).strip()
        is_unnamed = not column_name or column_name.casefold().startswith("unnamed:")
        if is_unnamed and dataframe[column].map(is_empty).all():
            columns_to_drop.append(column)

    if not columns_to_drop:
        return dataframe

    return dataframe.drop(columns=columns_to_drop)


def _drop_empty_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    mask = dataframe.apply(lambda row: all(is_empty(value) for value in row), axis=1)
    return dataframe.loc[~mask]


def _drop_rows_empty_in_columns(
    dataframe: pd.DataFrame, columns: list[str]
) -> pd.DataFrame:
    mask = dataframe[columns].apply(
        lambda row: all(is_empty(value) for value in row), axis=1
    )
    return dataframe.loc[~mask]


class _BalancedHTMLParser(HTMLParser):
    _VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.open_tags: list[str] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.casefold()
        if tag not in self._VOID_TAGS:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag: str, attrs) -> None:
        return None

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        if tag in self._VOID_TAGS:
            return

        if not self.open_tags:
            self.errors.append(f"tag </{tag}> fechada sem abertura")
            return

        expected = self.open_tags.pop()
        if expected != tag:
            self.errors.append(
                f"esperado fechamento de <{expected}>, mas encontrado </{tag}>"
            )
