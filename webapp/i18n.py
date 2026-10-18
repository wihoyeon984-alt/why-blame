"""User-interface translations for the local web dashboard."""

SUPPORTED_LANGUAGES = {
    "en": "English",
    "ko": "한국어",
}

DEFAULT_LANGUAGE = "en"

TEXT = {
    "en": {
        "language": "Language",
        "subtitle": "Code History & Evidence Explorer",
        "description": (
            "Explore code history and the evidence behind each explanation."
        ),
        "repository_path": "Git repository path",
        "file_path": "File path",
        "file_path_help": "Use a path relative to the repository root.",
        "start_line": "Start line",
        "end_line": "End line",
        "start_analysis": "Start analysis",
        "analyzing": "Analyzing Git history...",
        "analysis_result": "Analysis result",
        "target": "Target",
        "file": "File",
        "lines": "Lines",
        "unknown_file": "Unknown file",
        "current_code": "Current code",
        "no_current_lines": "No current source lines were returned.",
        "evidence_summary": "Evidence summary",
        "confidence": "Confidence",
        "coverage": "Coverage",
        "evidence_events": "Evidence events",
        "rollbacks": "Rollbacks",
        "not_provided": "Not provided",
        "detailed_statistics": "Detailed evidence statistics",
        "no_statistics": "No summary statistics were returned.",
        "change_history": "Change history",
        "evidence_event": "Evidence event {index}",
        "date": "Date",
        "commit": "Commit",
        "type": "Type",
        "diff_evidence": "Diff evidence",
        "references": "References",
        "full_event_details": "Full event details",
        "no_timeline": "No timeline events were returned.",
        "raw_json": "Raw JSON",
        "download_json": "Download JSON",
        "easy_explanation": "Easy explanation",
        "developer_details": "Developer details",
        "easy_explanation_fallback": (
            "This result does not contain structured evidence for an easy "
            "explanation. You can inspect the original analysis under "
            "Developer details."
        ),
        "easy_target_question": "Where is the selected code?",
        "easy_target_not_repeated": (
            "The selected target is shown in the Developer details tab."
        ),
        "easy_reason_question": (
            "Can the reason for the change be found in the recorded evidence?"
        ),
        "easy_evidence_question": "What sources were checked?",
        "easy_unknown_question": (
            "What cannot be established from the recorded evidence?"
        ),
        "easy_limitations_question": "Analysis limitations",
        "easy_reason_explicit_text": (
            "The body explanation in a related record was checked. However, "
            "its content does not guarantee the author's full intent."
        ),
        "easy_reason_title_only": (
            "The title of a related record was checked, but a specific "
            "change reason cannot be established from a title alone."
        ),
        "easy_reason_not_recorded": (
            "A specific change reason cannot be established from the "
            "recorded evidence."
        ),
        "easy_reason_withheld": (
            "The explanation was withheld because the evidence was "
            "insufficient or inconsistent."
        ),
        "easy_channel_target_code": "selected code",
        "easy_channel_code_diff": "code difference",
        "easy_channel_commit_title": "commit title",
        "easy_channel_pr_title": "pull request title",
        "easy_channel_pr_body": "pull request body",
        "easy_channel_issue_title": "issue title",
        "easy_channel_issue_body": "issue body",
        "easy_support_behavior": "code behavior",
        "easy_support_reason": "change context",
        "easy_support_none": "record only",
        "easy_unknown_developer_intent": (
            "The developer's full intent was not recorded."
        ),
        "easy_unknown_change_reason": (
            "The specific change reason was not recorded."
        ),
        "easy_unknown_truncated_context": (
            "Some reference context was only partially available."
        ),
        "easy_unknown_information": (
            "Some information could not be established from this analysis."
        ),
        "easy_limitation_history_partial": (
            "Only part of the relevant history may be available."
        ),
        "easy_limitation_rollback_history": (
            "Rollback history makes the sequence harder to interpret."
        ),
        "easy_unknown_limitation": (
            "Some analysis limitations could not be described in detail."
        ),
        "easy_origin_observed": (
            "A first appearance was found in the inspected Git history. "
            "Earlier history may be missing because of file moves or splits."
        ),
        "easy_truncated_notice": (
            "This source is only partially available and was not used alone "
            "to reach a conclusion."
        ),
        "easy_no_evidence": (
            "This analysis did not find material that can explain the "
            "reason for the change."
        ),
        "easy_history_origin": "What was observed in history",
        "easy_no_limitations": (
            "No separate limitation codes were recorded. However, this "
            "analysis cannot establish or guarantee unrecorded developer "
            "intent or behavior outside the selected code range."
        ),
        "easy_target_unavailable": (
            "The analysis target information could not be confirmed."
        ),
        "easy_behavior_question": "What was confirmed in this code?",
        "easy_behavior_fallback": (
            "This result does not include structured information for "
            "explaining the current code behavior."
        ),
        "easy_behavior_status_direct": (
            "This behavior was directly confirmed in the selected code."
        ),
        "easy_behavior_status_partial": (
            "Only part of this behavior was confirmed in the current code. "
            "Unverified parts are not presented as a complete behavior."
        ),
        "easy_behavior_status_not_established": (
            "A complete beginner-facing behavior could not be established "
            "from the selected code."
        ),
        "easy_behavior_status_withheld": (
            "The behavior explanation was withheld because the evidence "
            "was insufficient or inconsistent."
        ),
        "easy_behavior_observation_direct": (
            "Directly confirmed in the selected code."
        ),
        "easy_behavior_observation_partial": (
            "Only partly confirmed in the selected code."
        ),
        "easy_behavior_unknown_outside_range": (
            "Behavior outside the selected code range is not guaranteed "
            "by this analysis."
        ),
        "easy_behavior_unknown_information": (
            "Some information could not be established from the selected "
            "code."
        ),
        "easy_behavior_limitation_withheld": (
            "The behavior explanation was withheld because the evidence "
            "was insufficient or inconsistent."
        ),
        "easy_behavior_limitation_partial": (
            "Part of the behavior could not be confirmed from the current "
            "code."
        ),
        "easy_behavior_limitation_not_established": (
            "Part of the behavior could not be confirmed from the current "
            "code."
        ),
        "easy_behavior_limitation_unknown": (
            "Part of the behavior could not be confirmed from the current "
            "code."
        ),
        "process_exit": "Why-Blame exited with code {exit_code}.",
        "error_repository_not_found": (
            "The repository path must be an existing directory."
        ),
        "error_not_a_git_repository": (
            "The repository path must be a Git work tree."
        ),
        "error_file_path_required": "The file path is required.",
        "error_absolute_file_path": (
            "The file path must be relative to the repository."
        ),
        "error_path_outside_repository": (
            "The file path must stay inside the repository."
        ),
        "error_file_not_found": "The requested file does not exist.",
        "error_start_line_not_integer": (
            "The start line must be an integer."
        ),
        "error_end_line_not_integer": (
            "The end line must be an integer."
        ),
        "error_nonpositive_line": "Line numbers must be at least 1.",
        "error_reversed_line_range": (
            "The start line cannot exceed the end line."
        ),
        "error_analysis_timeout": "Why-Blame analysis timed out.",
        "error_analysis_start_failed": (
            "Why-Blame analysis could not be started."
        ),
        "error_unexpected_stderr": (
            "Why-Blame unexpectedly wrote to stderr."
        ),
        "error_output_not_ascii_safe": (
            "Why-Blame output was not ASCII-safe."
        ),
        "error_invalid_json": (
            "Why-Blame did not return valid JSON."
        ),
        "error_json_not_object": (
            "Why-Blame JSON must be an object."
        ),
        "error_unsupported_schema": (
            "Unsupported Why-Blame JSON schema."
        ),
    },
    "ko": {
        "language": "언어",
        "subtitle": "코드 변경 이력과 근거 탐색",
        "description": (
            "코드 변경 이력과 각 설명을 뒷받침하는 근거를 확인합니다."
        ),
        "repository_path": "Git 저장소 경로",
        "file_path": "파일 경로",
        "file_path_help": "저장소 루트를 기준으로 한 상대 경로를 입력하세요.",
        "start_line": "시작 줄",
        "end_line": "끝 줄",
        "start_analysis": "분석 시작",
        "analyzing": "Git 변경 이력을 분석하는 중...",
        "analysis_result": "분석 결과",
        "target": "분석 대상",
        "file": "파일",
        "lines": "줄 범위",
        "unknown_file": "알 수 없는 파일",
        "current_code": "현재 코드",
        "no_current_lines": "현재 소스 코드가 반환되지 않았습니다.",
        "evidence_summary": "근거 요약",
        "confidence": "신뢰도",
        "coverage": "근거 범위",
        "evidence_events": "근거 이력",
        "rollbacks": "되돌리기 기록",
        "not_provided": "제공되지 않음",
        "detailed_statistics": "상세 근거 통계",
        "no_statistics": "요약 통계가 반환되지 않았습니다.",
        "change_history": "변경 이력",
        "evidence_event": "근거 이벤트 {index}",
        "date": "날짜",
        "commit": "커밋",
        "type": "유형",
        "diff_evidence": "Diff 근거",
        "references": "참조",
        "full_event_details": "전체 이벤트 상세 정보",
        "no_timeline": "변경 이력 이벤트가 반환되지 않았습니다.",
        "raw_json": "원본 JSON",
        "download_json": "JSON 다운로드",
        "easy_explanation": "쉬운 설명",
        "developer_details": "개발자 상세",
        "easy_explanation_fallback": (
            "이 분석 결과에는 쉬운 설명을 만들기 위한 구조화된 근거가 "
            "없습니다. 개발자 상세에서 원본 분석 결과를 확인할 수 있습니다."
        ),
        "easy_target_question": "선택한 코드는 어디인가요?",
        "easy_target_not_repeated": (
            "선택한 대상은 개발자 상세 탭에서 확인할 수 있습니다."
        ),
        "easy_reason_question": (
            "변경 이유를 기록에서 확인할 수 있나요?"
        ),
        "easy_evidence_question": "어떤 자료를 확인했나요?",
        "easy_unknown_question": (
            "확인된 기록에서는 무엇을 알 수 없나요?"
        ),
        "easy_limitations_question": "분석의 제한사항",
        "easy_reason_explicit_text": (
            "관련 기록의 본문 설명을 확인했습니다. 다만 기록의 내용이 "
            "실제 작성자의 전체 의도를 보장하지는 않습니다."
        ),
        "easy_reason_title_only": (
            "관련 기록의 제목은 확인했지만, 제목만으로 구체적인 변경 "
            "이유를 확정할 수 없습니다."
        ),
        "easy_reason_not_recorded": (
            "확인된 기록에서는 구체적인 변경 이유를 알 수 없습니다."
        ),
        "easy_reason_withheld": (
            "근거가 부족하거나 서로 맞지 않아 변경 이유 설명을 보류했습니다."
        ),
        "easy_channel_target_code": "선택한 코드",
        "easy_channel_code_diff": "코드 차이",
        "easy_channel_commit_title": "커밋 제목",
        "easy_channel_pr_title": "풀 리퀘스트 제목",
        "easy_channel_pr_body": "풀 리퀘스트 본문",
        "easy_channel_issue_title": "이슈 제목",
        "easy_channel_issue_body": "이슈 본문",
        "easy_support_behavior": "코드 동작",
        "easy_support_reason": "변경 맥락",
        "easy_support_none": "기록 자체",
        "easy_unknown_developer_intent": (
            "개발자의 전체 의도는 기록되지 않았습니다."
        ),
        "easy_unknown_change_reason": (
            "확인된 기록에서는 구체적인 변경 이유를 알 수 없습니다."
        ),
        "easy_unknown_truncated_context": (
            "참조 자료의 일부 맥락만 확인할 수 있었습니다."
        ),
        "easy_unknown_information": (
            "이 분석에서 확인하지 못한 정보가 있습니다."
        ),
        "easy_limitation_history_partial": (
            "관련 이력의 일부만 확인할 수 있을 수 있습니다."
        ),
        "easy_limitation_rollback_history": (
            "되돌리기 이력으로 변경 순서를 해석하기 어렵습니다."
        ),
        "easy_unknown_limitation": (
            "일부 분석 제한사항을 자세히 설명할 수 없습니다."
        ),
        "easy_origin_observed": (
            "확인된 Git 이력에서 처음 나타난 기록이 있습니다. "
            "파일 이동이나 분리 이전 기록은 포함되지 않을 수 있습니다."
        ),
        "easy_truncated_notice": (
            "일부만 표시된 자료입니다. 이 내용만으로 결론을 내리지 않았습니다."
        ),
        "easy_no_evidence": (
            "이번 분석에서는 변경 이유를 설명할 수 있는 자료를 "
            "확인하지 못했습니다."
        ),
        "easy_history_origin": "이력에서 확인된 내용",
        "easy_no_limitations": (
            "별도의 제한사항 코드는 기록되지 않았습니다. 다만 기록되지 "
            "않은 개발자의 의도와 선택한 코드 범위 밖의 동작은 이 분석으로 "
            "확인하거나 보장할 수 없습니다."
        ),
        "easy_target_unavailable": (
            "분석 대상 정보를 확인할 수 없습니다."
        ),
        "easy_behavior_question": "이 코드에서 무엇을 확인했나요?",
        "easy_behavior_fallback": (
            "이 분석 결과에는 현재 코드 동작을 설명하기 위한 구조화된 "
            "정보가 없습니다."
        ),
        "easy_behavior_status_direct": (
            "현재 선택한 코드에서 직접 확인한 동작입니다."
        ),
        "easy_behavior_status_partial": (
            "현재 코드에서 동작의 일부만 확인했습니다. 확인되지 않은 부분을 "
            "포함해 전체 동작으로 단정하지 않습니다."
        ),
        "easy_behavior_status_not_established": (
            "현재 선택한 코드에서 초보자용으로 설명할 수 있는 완전한 동작을 "
            "확인하지 못했습니다."
        ),
        "easy_behavior_status_withheld": (
            "근거가 부족하거나 서로 맞지 않아 코드 동작 설명을 보류했습니다."
        ),
        "easy_behavior_observation_direct": (
            "선택한 코드에서 직접 확인했습니다."
        ),
        "easy_behavior_observation_partial": (
            "선택한 코드에서 일부만 확인했습니다."
        ),
        "easy_behavior_unknown_outside_range": (
            "선택한 코드 범위 밖의 동작은 이 분석으로 보장할 수 없습니다."
        ),
        "easy_behavior_unknown_information": (
            "현재 코드에서 확인하지 못한 정보가 있습니다."
        ),
        "easy_behavior_limitation_withheld": (
            "근거가 부족하거나 서로 맞지 않아 코드 동작 설명을 보류했습니다."
        ),
        "easy_behavior_limitation_partial": (
            "현재 코드만으로는 동작의 일부를 확인할 수 없습니다."
        ),
        "easy_behavior_limitation_not_established": (
            "현재 코드만으로는 동작의 일부를 확인할 수 없습니다."
        ),
        "easy_behavior_limitation_unknown": (
            "현재 코드만으로는 동작의 일부를 확인할 수 없습니다."
        ),
        "process_exit": "Why-Blame이 종료 코드 {exit_code}(으)로 종료되었습니다.",
        "error_repository_not_found": (
            "저장소 경로에 존재하는 디렉터리를 지정해야 합니다."
        ),
        "error_not_a_git_repository": (
            "선택한 경로는 Git 작업 트리가 아닙니다."
        ),
        "error_file_path_required": "파일 경로를 입력해야 합니다.",
        "error_absolute_file_path": (
            "파일 경로는 저장소 기준 상대 경로여야 합니다."
        ),
        "error_path_outside_repository": (
            "파일 경로는 저장소 내부에 있어야 합니다."
        ),
        "error_file_not_found": "요청한 파일이 존재하지 않습니다.",
        "error_start_line_not_integer": (
            "시작 줄은 정수여야 합니다."
        ),
        "error_end_line_not_integer": (
            "끝 줄은 정수여야 합니다."
        ),
        "error_nonpositive_line": "줄 번호는 1 이상이어야 합니다.",
        "error_reversed_line_range": (
            "시작 줄은 끝 줄보다 클 수 없습니다."
        ),
        "error_analysis_timeout": (
            "Why-Blame 분석 시간이 제한을 초과했습니다."
        ),
        "error_analysis_start_failed": (
            "Why-Blame 분석을 시작할 수 없습니다."
        ),
        "error_unexpected_stderr": (
            "Why-Blame이 예기치 않은 진단 출력을 생성했습니다."
        ),
        "error_output_not_ascii_safe": (
            "Why-Blame 출력을 안전하게 해석할 수 없습니다."
        ),
        "error_invalid_json": (
            "Why-Blame이 올바른 JSON을 반환하지 않았습니다."
        ),
        "error_json_not_object": (
            "Why-Blame JSON 결과는 객체여야 합니다."
        ),
        "error_unsupported_schema": (
            "지원하지 않는 Why-Blame JSON 스키마입니다."
        ),
    },
}


def translate(language, key, **values):
    """Return a translated UI string.

    Unknown languages fall back to English. Missing translation keys raise
    KeyError so incomplete translation dictionaries fail during development.
    """
    selected_language = (
        language
        if language in SUPPORTED_LANGUAGES
        else DEFAULT_LANGUAGE
    )
    message = TEXT[selected_language][key]
    return message.format(**values)


def translate_error(language, error):
    """Translate a coded UI error and preserve unknown messages."""
    code = getattr(error, "code", None)

    if not isinstance(code, str) or not code:
        return str(error)

    key = "error_" + code.lower()

    try:
        return translate(language, key)
    except KeyError:
        return str(error)
