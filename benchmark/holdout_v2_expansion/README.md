# Holdout v2 Expansion

This directory contains new evaluation cases that are intentionally isolated
from the frozen Holdout v2 baseline and post-improvement comparison.

## Evaluation boundary

The following directories remain frozen and must not be modified when adding
an expansion case:

- `benchmark/holdout_v2/cases`
- `benchmark/holdout_v2/annotations`
- `benchmark/holdout_v2/post_improvement`
- preserved Holdout v2 summaries and metadata

Expansion cases must be stored only under this directory.

## Required case workflow

Each expansion case must follow this order:

1. Select a previously unused public repository revision and code range.
2. Write and validate the Ground Truth case.
3. Commit the Ground Truth before running Why-Blame.
4. Preserve the first-run stdout, stderr, and metadata.
5. Commit the first-run artifacts without rewriting them.
6. Write the annotation using only the preserved execution output.
7. Commit the annotation.
8. Score the expansion cohort separately from the frozen Holdout v2 cohort.

Git history must demonstrate that Ground Truth was frozen before the first
analysis execution.

## Directory layout

- `cases/`: frozen Ground Truth case documents
- `runs/<case_id>/`: preserved first-run stdout, stderr, and metadata
- `annotations/`: annotations written after the first run

Case and annotation files use the existing Holdout v2 schema version 2 unless
a future expansion-specific schema is explicitly introduced.

## WITHHELD reasons

A `WITHHELD` claim may use an optional `withheld_reason` only when the reason
is directly observable from the preserved execution artifact.

Allowed identifiers:

- `INSUFFICIENT_EVIDENCE`
- `CONFLICTING_EVIDENCE`
- `NOT_OBSERVED`
- `OUTSIDE_SUPPORTED_SCOPE`

Safety rules:

- Do not derive a reason from the Ground Truth label.
- Do not equate `WITHHELD` with `UNSUPPORTED`.
- Do not treat `NOT_OBSERVED` as evidence that a claim is false.
- Do not infer a conflict from commit or PR text alone.
- Omit `withheld_reason` when the preserved artifact does not establish one.

## Isolation requirement

The frozen Holdout v2 scorer must not automatically discover expansion cases.

Expansion results must be reported separately. A future expansion scorer may
reuse the existing case, annotation, validation, confidence, metric, and report
modules, but it must receive expansion directories explicitly.

## Prohibited changes

Adding an expansion case must not:

- update the frozen Holdout v2 expected summary;
- change the preserved baseline or post-improvement metrics;
- rewrite existing Holdout v2 annotations;
- add inferred reasons to historical annotations;
- change the public CLI JSON schema;
- select cases primarily to improve an aggregate metric.

## Scoring

Run the isolated expansion scorer with:

```powershell
python .\benchmark\holdout_v2_expansion\score_expansion.py
```

The command reads only:

- benchmark/holdout_v2_expansion/cases
- benchmark/holdout_v2_expansion/annotations

The command fails when the expansion cohort is empty, when case and annotation
IDs disagree, or when frozen Holdout v2 directories are supplied.

The expansion scorer reuses the existing Holdout v2 schema validation,
confidence metrics, and WITHHELD reason-coverage report. Expansion results
must not be compared with the frozen post-improvement summary as if they were
part of the same cohort.
