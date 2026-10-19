# why-blame

[한국어 안내](README.ko.md)

> **Git blame tells you WHO. Why-blame shows the evidence behind WHY.**

`why-blame` is a CLI tool for reconstructing how code reached its current form
from Git history, diffs, commits, pull requests, issues, and other available
evidence.

The project follows a conservative rule:

> **Related is not the same as proven.**

A related commit, pull request, issue, symbol, or nearby implementation is not
automatically treated as proof of a causal explanation.

When available evidence does not support a specific WHY, `why-blame` should
withhold or explicitly qualify that explanation rather than invent a plausible
reason.

## What Why-Blame Tries to Answer

Traditional `git blame` is useful for questions such as:

> Who last changed this line?

`why-blame` investigates a different question:

> What observable history and evidence explain how this code reached its
> current form?

Why-Blame separates current behavior, physical diffs, commit descriptions,
linked PRs and issues, historical evolution, reversions, and contextual
evidence rather than treating every related artifact as proof of developer
intent.

## Evidence and Safety Pipeline

The current semantic path is:

```text
Structured Semantics
        |
        v
Evidence Entailment
        |
        v
Contradiction Check
        |
        v
Safety Gate
        |
        v
Safe Rendering
```

## Current Development Status

This section describes the current state of the latest `main` branch.

- Test suite: `574 / 574`
- CI: `6 / 6`
- Development branch: `main`

The documentation below includes multiple evaluation sources:

- Current development branch status
- Stable release validation snapshots
- Holdout v1 frozen benchmark results
- Holdout v2 frozen benchmark results
- External generalization evaluation reports

These sections were produced from different evaluation sets and points in time and should not be interpreted as a single measurement.

## Empirical Validation

Why-Blame includes a frozen **Holdout v1** benchmark:

```text
10 open-source cases
55 frozen Ground Truth claims

SUPPORTED:    32
UNSUPPORTED:  19
AMBIGUOUS:     4
CONFLICTING:   0

Required abstentions: 23
```

Both evaluations have complete annotations:

```text
First-run: 55 / 55 claims
Current:   55 / 55 claims
```

### Holdout v1 Results

| Metric | First-run | Current |
|---|---:|---:|
| E2E completion | 0.000 | **1.000** |
| Strict supported recall | 0.688 | **0.781** |
| Observed supported recall | 0.688 | **0.781** |
| Unobservable claim rate | 0.000 | 0.000 |
| Safe claim coverage | 0.400 | **0.455** |
| Abstention precision | 0.778 | **1.000** |
| Abstention recall | **0.304** | 0.130 |
| Unsafe presented | **0** | **0** |

Supported-claim recovery improved from `22 / 32` to `25 / 32`.

E2E completion improved from `0 / 10` to `10 / 10`, while `unsafe_presented`
remained zero.
### Known Trade-off

The current result is not uniformly better on every metric.

Explicit abstention precision improved from `0.778` to `1.000`, but explicit
abstention recall decreased from `0.304` to `0.130`.

Current suppression behavior is:

```text
Required abstentions: 23
Explicit abstentions:  3
Correct abstentions:   3
WITHHELD:              20
Safe suppressions:     23
```

## Reproducing the Benchmark

Frozen first-run baseline:

```powershell
python .\benchmark\holdout\score_holdout.py
```

Current evaluation:

```powershell
python .\benchmark\holdout\score_holdout.py --run current
```

Both evaluations use the same frozen Ground Truth, annotation validation, and metric calculation.

For detailed methodology, annotations, trade-offs, and failure analysis, see `benchmark/holdout/REPORT.md`.

## Current Known Failure Classes

Seven SUPPORTED claims remain unrecovered in the current Holdout v1
evaluation. See `benchmark/holdout/REPORT.md` and the frozen annotations for
case-level results and evaluation methodology.


## Latest release

The latest stable release is why-blame v0.3.6.

The metrics below were recorded at release time and do not represent the current `main` branch.

Release-time validation snapshot for v0.3.6:
- 278 unit tests passed
- 10/10 holdout cases completed
- 87.5% strict supported recall
- 0 unsafe presented claims
- 0 False-WHY results
- Windows and Linux CI support
- Python 3.9, 3.11, and 3.14 support

## Installation

Requirements:

- Python 3.9 or later
- Git

Clone and install the current development branch:

```powershell
git clone https://github.com/wihoyeon984-alt/why-blame.git
cd why-blame
git switch main
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

The editable installation was verified in a clean virtual environment.
The installed CLI was also verified outside the repository directory.

## Usage

Show CLI help:

```powershell
why-blame --help
```

Supported forms:

```text
why-blame FILE:LINE
why-blame FILE:START-END
why-blame FILE LINE
why-blame FILE START END
```

Examples:

```powershell
why-blame service.py:10
why-blame service.py:1-3
why-blame service.py 10
why-blame service.py 1 3
```

The target file should belong to a Git repository with relevant history.

### JSON output

Use `--json` when another program consumes the analysis result.

```powershell
why-blame service.py:10 --json
why-blame --json service.py:10
```

Without `--json`, Why-Blame keeps the human-readable card output.
JSON mode writes one JSON document to standard output.

```json
{
  "schema_version": "1",
  "target": {
    "file": "service.py",
    "start_line": 10,
    "end_line": 10
  },
  "repository": null,
  "current_lines": [],
  "timeline": [],
  "stats": {}
}
```

- `schema_version` identifies the public JSON schema.
- `target` contains the requested file and inclusive line range.
- `repository` contains repository metadata, or `null`.
- `current_lines` contains the current source lines.
- `timeline` contains the oldest-to-newest evidence history.
- `stats` contains confidence, coverage, and limitations.

The raw output is ASCII-safe. A JSON parser restores escaped Unicode.

`--json` may appear before or after the target, but only once.
It cannot be combined with help or version options.

#### JSON error responses

When JSON mode fails, standard output contains one JSON document:

```json
{
  "schema_version": "1",
  "error": {
    "code": "FILE_NOT_FOUND",
    "message": "The requested file does not exist: missing.py"
  }
}
```

JSON errors use exit code `1` for analysis or runtime failures and exit
code `2` for invalid command-line arguments. Standard error remains empty.

#### JSON error codes

- `INVALID_ARGUMENTS` uses exit code `2`. The command-line arguments are
  missing, duplicated, incompatible, or invalid. Correct the command and
  run it again. Retrying the same command without changes will not help.
- `NO_HISTORY` uses exit code `1`. Git completed successfully, but no
  relevant history was found. Check the target range or repository history.
- `FILE_NOT_FOUND` uses exit code `1`. The requested path is not an existing
  file. Correct the path before retrying.
- `NOT_A_GIT_REPOSITORY` uses exit code `1`. The current directory is not
  inside a Git work tree. Run Why-Blame from the target repository.
- `LINE_RANGE_OUT_OF_BOUNDS` uses exit code `1`. The requested line or range
  exceeds the current file length. Choose a valid inclusive line range.
- `FILE_READ_ERROR` uses exit code `1`. The file exists but cannot be read,
  for example because of permissions, an operating-system error, or invalid
  UTF-8. Fix file access or encoding before retrying.
- `GIT_COMMAND_FAILED` uses exit code `1`. Git history analysis failed, such
  as for an untracked file or an invalid Git state. Review the error message,
  commit or track the file when appropriate, and then retry.

Automation should branch on `error.code`, not on localized message text.
The `message` field is diagnostic and may include relevant file or Git
details. The public error schema remains identified by `schema_version`.

### Web dashboard

Why-Blame includes a local Streamlit dashboard that reuses the existing
JSON analysis engine.

Install and run the dashboard with:

    python -m venv .venv-web
    .\.venv-web\Scripts\python.exe -m pip install -r .\requirements-web.txt
    .\.venv-web\Scripts\python.exe -m streamlit run .\webapp\app.py

Open http://localhost:8501 if the browser does not open automatically.

Enter a local Git repository, a repository-relative file path, and an
inclusive line range. The dashboard displays current code, evidence summary,
limitations, change history, raw JSON, and a JSON download button.

Use the language selector at the top of the dashboard to switch between
English and Korean. Changing the display language preserves the current
analysis result. JSON field names, error codes, confidence levels, and other
machine-readable values remain unchanged.

The initial dashboard is intended for local use.

## Testing

The project currently passes `574 / 574` tests.


The Holdout scorer-specific suite passes `18 / 18` tests.

### Holdout v2 evaluation snapshot

The recorded Holdout v2 post-improvement metrics cover 10 frozen cases,
40 Ground Truth claims, and 20 Supported Ground Truth claims. The recorded
result presented `20 / 20` Supported claims, with claim precision `1.000`,
supported recall `1.000`, and unsafe presentation rate `0.000`.

> These metrics were produced by Why-Blame commit
> `38316d107b848ea98713a486d2e0332540dfb140`. They are preserved as a
> reproducible evaluation snapshot and should not be interpreted as a fresh
> measurement of the current `main` branch or as guaranteed performance on
> repositories, languages, code structures, or histories outside the frozen
> evaluation set.

## Development Policy

Future semantic changes should be motivated by repeated observable failures rather than repository-specific benchmark rules.

The preferred loop is: observe failure -> identify a reusable failure class -> write a synthetic regression test -> implement a bounded change -> run the full regression suite -> re-score the frozen Holdout -> check recovery and safety together.

Recall improvements should not be accepted by themselves if they increase unsupported explanations.

## Project Principle

> **Explain what the available evidence can support, and stop where the evidence stops.**

> **Related is not the same as proven.**
