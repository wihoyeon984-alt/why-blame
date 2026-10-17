import json
from pathlib import Path

import streamlit as st

from webapp.result_view import (
    ErrorView,
    ResultViewError,
    SuccessView,
    build_result_view,
)
from webapp.runner import DashboardRunError, run_analysis
from webapp.validators import ValidationError, validate_target


st.set_page_config(
    page_title="Why-Blame Dashboard",
    page_icon="WB",
    layout="wide",
)

st.title("WHY-BLAME")
st.subheader("Code History & Evidence Explorer")
st.write(
    "Explore code history and the evidence behind each explanation."
)

default_repository = str(Path.cwd())


with st.form("analysis-form"):
    repository_path = st.text_input(
        "Git repository path",
        value=default_repository,
    )

    file_path = st.text_input(
        "File path",
        value="service.py",
        help="Use a path relative to the repository root."
    )

    start_column, end_column = st.columns(2)

    with start_column:
        start_line = st.number_input(
            "Start line",
            min_value=1,
            value=1,
            step=1,
        )

    with end_column:
        end_line = st.number_input(
            "End line",
            min_value=1,
            value=1,
            step=1,
        )

    submitted = st.form_submit_button(
        "Start analysis",
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
        st.error(str(exc))
    else:
        try:
            with st.spinner("Analyzing Git history..."):
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
            st.error(str(exc))
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
            f"Why-Blame exited with code {stored_analysis.exit_code}."
        )


if isinstance(stored_view, SuccessView):
    st.divider()
    st.header("Analysis result")

    target = stored_view.target
    target_file = target.get("file", "Unknown file")
    target_start = target.get("start_line", "?")
    target_end = target.get("end_line", "?")

    st.subheader("Target")
    st.write("File:", target_file)
    st.write("Lines:", f"{target_start}-{target_end}")

    st.subheader("Current code")

    if stored_view.current_lines:
        display_lines = list(
            stored_view.current_lines
        )
        display_lines[0] = display_lines[0].lstrip("\ufeff")

        source_text = "\n".join(
            display_lines
        )
        st.code(
            source_text,
            language="python",
            line_numbers=True,
        )
    else:
        st.info("No current source lines were returned.")

    st.subheader("Evidence summary")

    if stored_view.stats:
        stats = stored_view.stats
        columns = st.columns(4)

        columns[0].metric(
            "Confidence",
            stats.get("confidence", "Not provided"),
        )
        columns[1].metric(
            "Coverage",
            stats.get("coverage", "Not provided"),
        )
        columns[2].metric(
            "Evidence events",
            stats.get("total_events", "Not provided"),
        )
        columns[3].metric(
            "Rollbacks",
            stats.get("reverts_count", "Not provided"),
        )

        limitations = stats.get("limitations", [])

        if limitations:
            st.warning(
                "\n".join(
                    f"- {item}"
                    for item in limitations
                )
            )

        with st.expander("Detailed evidence statistics"):
            st.json(stats)
    else:
        st.info("No summary statistics were returned.")

    st.subheader("Change history")

    if stored_view.timeline:
        for index, event in enumerate(
            stored_view.timeline,
            start=1,
        ):
            title = f"Evidence event {index}"

            if isinstance(event, dict):
                message = event.get("message")
                if message:
                    title = str(message)

            with st.expander(
                title,
                expanded=(index == 1),
            ):
                if isinstance(event, dict):
                    metadata = st.columns(3)

                    metadata[0].metric(
                        "Date",
                        event.get("date", "Not provided"),
                    )
                    metadata[1].metric(
                        "Commit",
                        event.get(
                            "short_hash",
                            "Not provided",
                        ),
                    )
                    metadata[2].metric(
                        "Type",
                        event.get("type", "Not provided"),
                    )

                    diff_lines = event.get(
                        "diff_lines",
                        [],
                    )

                    if diff_lines:
                        st.markdown("**Diff evidence**")
                        st.code(
                            "\n".join(diff_lines),
                            language="diff",
                        )

                    refs = event.get("refs", [])

                    if refs:
                        st.markdown(
                            "**References:** "
                            + ", ".join(
                                f"#{reference}"
                                for reference in refs
                            )
                        )

                    with st.expander(
                        "Full event details"
                    ):
                        st.json(event)
                else:
                    st.json(event)
    else:
        st.info("No timeline events were returned.")


if stored_analysis is not None:
    raw_json = json.dumps(
        stored_analysis.document,
        ensure_ascii=False,
        indent=2,
    )

    with st.expander("Raw JSON"):
        st.json(stored_analysis.document)

    st.download_button(
        "Download JSON",
        data=raw_json,
        file_name="why-blame-result.json",
        mime="application/json",
        use_container_width=True,
    )
