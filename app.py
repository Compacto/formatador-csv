from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

from services.exporter import (
    export_dataframe_to_csv_bytes,
    make_output_filename,
    save_csv,
    sanitize_domain,
)
from services.transformer import transform_dataframe
from services.validator import (
    LOAD_SPECS,
    LoadSpec,
    ValidationIssue,
    ValidationResult,
    get_load_spec,
    read_excel_file,
    validate_dataframe,
)


APP_TITLE = "Dataplex Metadata Loader"
NAV_GENERATOR = "Gerador CSV"
NAV_RULES = "Regras de Carga"


def main() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_theme()

    st.markdown(
        """
        <div class="top-nav">
            <strong>Dataplex Metadata Loader</strong>
            <span>Governança de Dados | XLSX para CSV Dataplex</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navegação",
        [NAV_GENERATOR, NAV_RULES],
        horizontal=True,
        label_visibility="collapsed",
    )

    if sys.version_info < (3, 12):
        st.warning("Esta aplicação foi preparada para Python 3.12 ou superior.")

    if page == NAV_RULES:
        render_rules_page()
    else:
        render_generator_page()


def render_generator_page() -> None:
    st.markdown(
        """
        <section class="hero">
            <span class="hero-kicker">Governança de Dados</span>
            <h1>Dataplex Metadata Loader</h1>
            <p>Valide templates Excel e gere CSVs prontos para ingestão de metadados no Dataplex.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    controls, details = st.columns([0.38, 0.62], gap="large")

    with controls:
        st.subheader("Tipo de carga")
        load_type = st.selectbox("Selecione o template", list(LOAD_SPECS.keys()))
        spec = get_load_spec(load_type)

        st.subheader("Upload")
        uploaded_file = st.file_uploader(
            "Selecionar arquivo XLSX",
            type=["xlsx"],
            accept_multiple_files=False,
            help="Apenas arquivos .xlsx são aceitos.",
        )

        validation_result = read_and_validate_upload(uploaded_file, spec)

        domain = None
        if spec.requires_domain:
            suggested_domain = infer_domain(validation_result, fallback="dominio")
            domain = st.text_input(
                "Domínio para o nome do arquivo",
                value=suggested_domain,
                help="Usado em overview-dataset-{dominio}.csv e overview-table-{dominio}.csv.",
            )

        with st.expander("Cabeçalho esperado", expanded=False):
            st.code("\n".join(spec.expected_columns), language="text")

        render_selected_template_download(spec)

    with details:
        if uploaded_file is None:
            render_empty_state(spec)
            return

        if validation_result is None:
            return

        render_validation_report(validation_result)

        with st.expander("Prévia da planilha validada", expanded=not validation_result.has_errors):
            st.dataframe(validation_result.dataframe.head(20), use_container_width=True)

        filename = make_output_filename(spec, domain)
        export_context = build_export_context(load_type, uploaded_file, filename)
        st.caption(f"Arquivo de saída: `{filename}`")

        generate_disabled = validation_result.has_errors
        if st.button("Gerar CSV", type="primary", disabled=generate_disabled):
            transformed = transform_dataframe(validation_result.dataframe, spec)
            csv_bytes = export_dataframe_to_csv_bytes(transformed)
            output_path = save_csv(csv_bytes, filename)
            st.session_state["last_export"] = {
                "context": export_context,
                "filename": filename,
                "csv_bytes": csv_bytes,
                "output_path": str(output_path.resolve()),
                "rows": len(transformed),
            }

        render_download_area(export_context)


def read_and_validate_upload(
    uploaded_file, spec: LoadSpec
) -> ValidationResult | None:
    if uploaded_file is None:
        return None

    if not uploaded_file.name.lower().endswith(".xlsx"):
        st.error("Arquivo inválido. Envie um template com extensão .xlsx.")
        return None

    try:
        dataframe = read_excel_file(uploaded_file)
    except Exception as exc:
        st.error(f"Não foi possível ler o XLSX: {exc}")
        return None

    return validate_dataframe(dataframe, spec)


def render_validation_report(result: ValidationResult) -> None:
    if result.errors:
        st.error(f"❌ {len(result.errors)} erro(s) encontrado(s)")
        render_issues_table(result.errors)
    else:
        st.success("✔ Arquivo válido")

    if result.warnings:
        st.info(
            f"{len(result.warnings)} ajuste(s) automático(s): campos vazios serão substituídos por NA."
        )
        render_issues_table(result.warnings)


def render_issues_table(issues: list[ValidationIssue]) -> None:
    rows = [
        {
            "Linha": "Cabeçalho" if issue.line is None else issue.line,
            "Campo": issue.field,
            "Descrição": issue.description,
        }
        for issue in issues
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_download_area(expected_context: str) -> None:
    export = st.session_state.get("last_export")
    if not export or export.get("context") != expected_context:
        return

    st.success(
        f"CSV gerado com {export['rows']} linha(s) e salvo em `{export['output_path']}`."
    )
    st.download_button(
        "Baixar CSV",
        data=export["csv_bytes"],
        file_name=export["filename"],
        mime="text/csv; charset=utf-8",
        type="primary",
    )


def render_selected_template_download(spec: LoadSpec) -> None:
    template_path = get_template_path(spec)
    if not template_path.exists():
        st.caption(f"Template não encontrado em `{template_path}`.")
        return

    st.download_button(
        "Baixar template deste tipo",
        data=template_path.read_bytes(),
        file_name=template_path.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


def get_template_path(spec: LoadSpec) -> Path:
    return Path("templates") / spec.template_filename


def render_empty_state(spec: LoadSpec) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <h3>Aguardando upload</h3>
            <p>Envie um arquivo XLSX do tipo <strong>{spec.label}</strong> para validar cabeçalho, campos obrigatórios e HTML antes da exportação.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rules_page() -> None:
    st.title("Regras de Carga")
    st.caption("Referência rápida para preparar templates antes da ingestão no Dataplex.")

    rule_columns = st.columns(2, gap="large")
    with rule_columns[0]:
        st.markdown(
            """
            <div class="rule-card">
                <h3>Conversão e separador</h3>
                <p>Todo XLSX é convertido para CSV UTF-8 com vírgula como separador. O app nunca usa ponto e vírgula como delimitador.</p>
            </div>
            <div class="rule-card">
                <h3>Campos obrigatórios</h3>
                <p>Campos vazios nas colunas finais são preenchidos automaticamente com <code>NA</code>. Linhas totalmente vazias são ignoradas.</p>
            </div>
            <div class="rule-card">
                <h3>Aspas</h3>
                <p>Campos com espaços, vírgulas, quebras de linha, aspas ou HTML recebem aspas automaticamente no CSV.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with rule_columns[1]:
        st.markdown(
            """
            <div class="rule-card">
                <h3>HTML para Overview</h3>
                <p>Overview - Dataset, Overview - Table e Glossário validam HTML não vazio, com tags abertas e fechadas corretamente.</p>
            </div>
            <div class="rule-card">
                <h3>Colunas operacionais</h3>
                <p><code>tipo de ação</code> e <code>justificativa</code> são aceitas nos templates operacionais e removidas antes da exportação.</p>
            </div>
            <div class="rule-card">
                <h3>Cabeçalhos</h3>
                <p>Todos os cabeçalhos obrigatórios precisam existir. Campos fora do template são reportados antes da geração.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Nomenclatura dos arquivos")
    filename_rows = [
        {
            "Tipo de carga": spec.label,
            "Template XLSX": spec.template_filename,
            "Arquivo gerado": spec.output_filename,
        }
        for spec in LOAD_SPECS.values()
    ]
    st.dataframe(pd.DataFrame(filename_rows), hide_index=True, use_container_width=True)

    st.subheader("Templates disponíveis")
    for spec in LOAD_SPECS.values():
        template_path = get_template_path(spec)
        if not template_path.exists():
            st.caption(f"{spec.label}: template não encontrado em `{template_path}`.")
            continue

        st.download_button(
            f"Baixar {template_path.name}",
            data=template_path.read_bytes(),
            file_name=template_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def infer_domain(result: ValidationResult | None, fallback: str) -> str:
    if result is None or result.dataframe.empty or "dataset" not in result.dataframe.columns:
        return fallback

    for value in result.dataframe["dataset"]:
        if pd.notna(value) and str(value).strip():
            return sanitize_domain(str(value))

    return fallback


def build_export_context(load_type: str, uploaded_file, filename: str) -> str:
    file_name = getattr(uploaded_file, "name", "")
    file_size = getattr(uploaded_file, "size", "")
    return f"{load_type}:{file_name}:{file_size}:{filename}"


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(20, 184, 166, 0.14), transparent 28rem),
                linear-gradient(135deg, #f8fafc 0%, #eef7f6 46%, #f5f7fb 100%);
            color: #102033;
        }

        .top-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.85rem 1rem;
            margin-bottom: 0.8rem;
            border-radius: 8px;
            background: #102033;
            color: #f8fafc;
        }

        .top-nav span {
            color: #b7c7d6 !important;
            font-size: 0.88rem;
        }

        .top-nav strong {
            color: #f8fafc !important;
        }

        [data-testid="stWidgetLabel"] p,
        div[role="radiogroup"] label p,
        div[role="radiogroup"] label span {
            color: #102033 !important;
            font-weight: 650;
        }

        [data-testid="stDownloadButton"] button,
        [data-testid="stDownloadButton"] button * {
            color: #f8fafc !important;
            font-weight: 700;
        }

        .hero {
            padding: 2rem;
            margin-bottom: 1.4rem;
            border-radius: 8px;
            background: linear-gradient(135deg, #0f766e 0%, #155e75 100%);
            color: #ffffff;
            box-shadow: 0 18px 45px rgba(15, 35, 51, 0.14);
        }

        .hero h1 {
            margin: 0.25rem 0 0.4rem 0;
            font-size: 2.2rem;
            letter-spacing: 0;
        }

        .hero p {
            max-width: 52rem;
            margin: 0;
            color: rgba(255, 255, 255, 0.88);
            font-size: 1.02rem;
        }

        .hero-kicker {
            display: inline-block;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.16);
            color: #d9fffb;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }

        .empty-state,
        .rule-card {
            padding: 1rem 1.1rem;
            margin-bottom: 0.9rem;
            border: 1px solid rgba(15, 118, 110, 0.16);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 10px 28px rgba(15, 35, 51, 0.08);
        }

        .empty-state h3,
        .rule-card h3 {
            margin: 0 0 0.35rem 0;
            color: #102033;
        }

        .empty-state p,
        .rule-card p {
            margin: 0;
            color: #425466;
        }

        code {
            color: #0f766e;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
