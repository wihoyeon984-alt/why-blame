import json
from pathlib import Path

import streamlit as st

from webapp.i18n import (
    SUPPORTED_LANGUAGES,
    translate,
    translate_error,
)
from webapp.result_view import (
    ErrorView,
    ResultViewError,
    SuccessView,
    build_result_view,
)
from webapp.beginner_explanation import (
    build_easy_explanation_sections,
)
from webapp.runner import DashboardRunError, run_analysis
from webapp.validators import ValidationError, validate_target


st.set_page_config(
    page_title="Why-Blame Dashboard",
    page_icon="WB",
    layout="wide",
)

st.title("WHY-BLAME")

current_language = st.session_state.get("ui_language", "en")

language = st.selectbox(
    translate(current_language, "language"),
    options=tuple(SUPPORTED_LANGUAGES),
    format_func=SUPPORTED_LANGUAGES.__getitem__,
    key="ui_language",
)


def t(key, **values):
    """Return UI text for the selected dashboard language."""
    return translate(language, key, **values)


def render_easy_explanation(
    beginner_evidence,
    beginner_behavior,
    target,
):
    sections = build_easy_explanation_sections(
        beginner_evidence,
        beginner_behavior,
        language,
        target,
    )

    if not sections["available"]:
        st.info(sections["fallback"])
        return

    if sections["behavior_available"]:
        st.subheader(t("easy_behavior_question"))
        st.write(sections["behavior_status"])

        for step in sections["behavior_steps"]:
            st.caption(step["observation_label"])
            st.write(step["statement"])
            if step["code_excerpt"]:
                st.code(step["code_excerpt"], language=None)
            for limitation in step["limitations"]:
                st.caption(limitation)

        for item in sections["behavior_unknown_items"]:
            st.write("- " + item)

        for item in sections["behavior_limitations"]:
            st.write("- " + item)
    else:
        st.subheader(t("easy_behavior_question"))
        st.info(sections["behavior_fallback"])

    st.subheader(sections["target_question"])
    st.write(sections["target_label"])

    st.subheader(sections["reason_question"])
    st.write(sections["reason_status"])

    st.subheader(sections["evidence_question"])
    if sections["evidence"]:
        for item in sections["evidence"]:
            st.write(item["label"] + ":")
            st.write(item["text"])
            if item["is_truncated"]:
                st.caption(sections["truncated_notice"])
    else:
        st.info(t("easy_no_evidence"))

    if sections["unknown_items"]:
        st.subheader(sections["unknown_question"])
        for item in sections["unknown_items"]:
            st.write("- " + item)

    if sections["origin"]:
        st.subheader(t("easy_history_origin"))
        st.write(sections["origin"])

    st.subheader(sections["limitations_question"])
    if sections["limitations"]:
        for item in sections["limitations"]:
            st.write("- " + item)
    else:
        st.info(t("easy_no_limitations"))


def render_developer_details(stored_view, stored_analysis):
    target = stored_view.target
    target_file = target.get("file", t("unknown_file"))
    target_start = target.get("start_line", "?")
    target_end = target.get("end_line", "?")

    st.subheader(t("target"))
    st.write(f"{t('file')}:", target_file)
    st.write(
        f"{t('lines')}:",
        f"{target_start}-{target_end}",
    )

    st.subheader(t("current_code"))

    if stored_view.current_lines:
        display_lines = list(stored_view.current_lines)
        display_lines[0] = display_lines[0].lstrip("\ufeff")
        st.code(
            "\n".join(display_lines),
            language="python",
            line_numbers=True,
        )
    else:
        st.info(t("no_current_lines"))

    st.subheader(t("evidence_summary"))

    if stored_view.stats:
        stats = stored_view.stats
        columns = st.columns(4)

        columns[0].metric(
            t("confidence"),
            stats.get("confidence", t("not_provided")),
        )
        columns[1].metric(
            t("coverage"),
            stats.get("coverage", t("not_provided")),
        )
        columns[2].metric(
            t("evidence_events"),
            stats.get("total_events", t("not_provided")),
        )
        columns[3].metric(
            t("rollbacks"),
            stats.get("reverts_count", t("not_provided")),
        )

        limitations = stats.get("limitations", [])
        if limitations:
            st.warning("\n".join(f"- {item}" for item in limitations))

        with st.expander(t("detailed_statistics")):
            st.json(stats)
    else:
        st.info(t("no_statistics"))

    st.subheader(t("change_history"))

    if stored_view.timeline:
        for index, event in enumerate(
            stored_view.timeline,
            start=1,
        ):
            title = t("evidence_event", index=index)
            if isinstance(event, dict):
                message = event.get("message")
                if message:
                    title = str(message)

            with st.expander(title, expanded=(index == 1)):
                if isinstance(event, dict):
                    metadata = st.columns(3)
                    metadata[0].metric(
                        t("date"),
                        event.get("date", t("not_provided")),
                    )
                    metadata[1].metric(
                        t("commit"),
                        event.get("short_hash", t("not_provided")),
                    )
                    metadata[2].metric(
                        t("type"),
                        event.get("type", t("not_provided")),
                    )

                    diff_lines = event.get("diff_lines", [])
                    if diff_lines:
                        st.markdown(f"**{t('diff_evidence')}**")
                        st.code(
                            "\n".join(diff_lines),
                            language="diff",
                        )

                    refs = event.get("refs", [])
                    if refs:
                        st.markdown(
                            f"**{t('references')}:** "
                            + ", ".join(f"#{reference}" for reference in refs)
                        )

                    with st.expander(t("full_event_details")):
                        st.json(event)
                else:
                    st.json(event)
    else:
        st.info(t("no_timeline"))

    if stored_analysis is not None:
        raw_json = json.dumps(
            stored_analysis.document,
            ensure_ascii=False,
            indent=2,
        )

        with st.expander(t("raw_json")):
            st.json(stored_analysis.document)

        st.download_button(
            t("download_json"),
            data=raw_json,
            file_name="why-blame-result.json",
            mime="application/json",
            use_container_width=True,
        )


st.subheader(t("subtitle"))
st.write(t("description"))

default_repository = str(Path.cwd())


with st.form("analysis-form"):
    repository_path = st.text_input(
        t("repository_path"),
        value=default_repository,
    )

    file_path = st.text_input(
        t("file_path"),
        value="service.py",
        help=t("file_path_help")
    )

    start_column, end_column = st.columns(2)

    with start_column:
        start_line = st.number_input(
            t("start_line"),
            min_value=1,
            value=1,
            step=1,
        )

    with end_column:
        end_line = st.number_input(
            t("end_line"),
            min_value=1,
            value=1,
            step=1,
        )

    submitted = st.form_submit_button(
        t("start_analysis"),
        type="primary",
        use_container_width=True,
    )


if submitted:
    try:
        target = validate_target(
            repository_path,
            file_path,
            int(start_line),
            int(end_line),
        )
    except ValidationError as exc:
        st.error(translate_error(language, exc))
    else:
        try:
            with st.spinner(t("analyzing")):
                analysis = run_analysis(
                    target.repository,
                    target.relative_file,
                    target.start_line,
                    target.end_line,
                )

            view = build_result_view(
                analysis.document
            )
        except (
            DashboardRunError,
            ResultViewError,
        ) as exc:
            st.error(translate_error(language, exc))
        else:
            st.session_state["analysis"] = analysis
            st.session_state["result_view"] = view


stored_view = st.session_state.get("result_view")
stored_analysis = st.session_state.get("analysis")

if isinstance(stored_view, ErrorView):
    st.divider()
    st.error(stored_view.message)
    st.code(stored_view.code, language=None)

    if stored_analysis is not None:
        st.caption(
            t(
                "process_exit",
                exit_code=stored_analysis.exit_code,
            )
        )


if isinstance(stored_view, SuccessView):
    st.divider()
    st.header(t("analysis_result"))
    easy_tab, developer_tab = st.tabs(
        [
            t("easy_explanation"),
            t("developer_details"),
        ]
    )

    with easy_tab:
        render_easy_explanation(
            stored_view.beginner_evidence,
            stored_view.beginner_behavior,
            stored_view.target,
        )

    with developer_tab:
        render_developer_details(
            stored_view,
            stored_analysis,
        )
