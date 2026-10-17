import json
from dataclasses import fields, is_dataclass


SCHEMA_VERSION = "1"


def _to_json_value(value):
    """Convert supported project values into JSON-compatible values."""
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _to_json_value(
                getattr(value, field.name)
            )
            for field in fields(value)
        }

    if isinstance(value, dict):
        return {
            str(key): _to_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _to_json_value(item)
            for item in value
        ]

    if isinstance(value, set):
        return [
            _to_json_value(item)
            for item in sorted(
                value,
                key=repr,
            )
        ]

    return value


def build_json_document(
    file_name,
    start_line,
    end_line,
    repo_info,
    current_lines,
    timeline,
    stats,
):
    repository = None

    if repo_info:
        owner, repo_name = repo_info
        repository = {
            "owner": owner,
            "name": repo_name,
        }

    return {
        "schema_version": SCHEMA_VERSION,
        "target": {
            "file": file_name,
            "start_line": start_line,
            "end_line": end_line,
        },
        "repository": repository,
        "current_lines": _to_json_value(
            current_lines
        ),
        "timeline": _to_json_value(
            timeline
        ),
        "stats": _to_json_value(
            stats
        ),
    }


def render_json(
    file_name,
    start_line,
    end_line,
    repo_info,
    current_lines,
    timeline,
    stats,
):
    document = build_json_document(
        file_name,
        start_line,
        end_line,
        repo_info,
        current_lines,
        timeline,
        stats,
    )

    print(
        json.dumps(
            document,
            ensure_ascii=True,
            indent=2,
        )
    )


def build_json_error_document(code, message):
    return {
        "schema_version": SCHEMA_VERSION,
        "error": {
            "code": code,
            "message": str(message),
        },
    }


def render_json_error(code, message):
    document = build_json_error_document(
        code,
        message,
    )

    print(
        json.dumps(
            document,
            ensure_ascii=True,
            indent=2,
        )
    )
