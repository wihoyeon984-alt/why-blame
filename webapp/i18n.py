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
