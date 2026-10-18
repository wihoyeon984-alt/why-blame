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
