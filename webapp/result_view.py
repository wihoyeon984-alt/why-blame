from dataclasses import dataclass


class ResultViewError(ValueError):
    pass


@dataclass(frozen=True)
class ErrorView:
    code: str
    message: str


@dataclass(frozen=True)
class SuccessView:
    target: dict
    repository: object
    current_lines: list
    timeline: list
    stats: dict


def build_error_view(document):
    error = document.get("error")

    if not isinstance(error, dict):
        raise ResultViewError(
            "The error object is missing."
        )

    code = error.get("code")
    message = error.get("message")

    if not isinstance(code, str) or not code:
        raise ResultViewError(
            "The error code is missing."
        )

    if not isinstance(message, str) or not message:
        raise ResultViewError(
            "The error message is missing."
        )

    return ErrorView(
        code=code,
        message=message,
    )


def build_success_view(document):
    target = document.get("target")
    current_lines = document.get("current_lines")
    timeline = document.get("timeline")
    stats = document.get("stats")

    if not isinstance(target, dict):
        raise ResultViewError(
            "The target object is missing."
        )

    if not isinstance(current_lines, list):
        raise ResultViewError(
            "The current lines are invalid."
        )

    if not isinstance(timeline, list):
        raise ResultViewError(
            "The timeline is invalid."
        )

    if not isinstance(stats, dict):
        raise ResultViewError(
            "The stats object is invalid."
        )

    return SuccessView(
        target=target,
        repository=document.get("repository"),
        current_lines=current_lines,
        timeline=timeline,
        stats=stats,
    )


def build_result_view(document):
    if not isinstance(document, dict):
        raise ResultViewError(
            "The analysis result must be an object."
        )

    if document.get("schema_version") != "1":
        raise ResultViewError(
            "Unsupported analysis schema."
        )

    if "error" in document:
        return build_error_view(document)

    return build_success_view(document)
