# Holdout v2 Evaluation

Holdout v2 extends the frozen Holdout v1 evaluation without modifying its
Ground Truth, preserved outputs, or scoring annotations.

## Goals

- Expand beyond 10 cases and 55 claims.
- Record case-level confidence explicitly.
- Report confidence-stratified metrics.
- Increase representation of low-confidence and blocked cases.
- Preserve claim precision and unsafe-presentation measurements.
- Keep execution reliability separate from semantic quality.

## Confidence levels

Internal confidence values use normalized identifiers:

- `VERY_HIGH`
- `HIGH`
- `MEDIUM`
- `LOW`
- `WEAK`
- `VERY_WEAK`
- `BLOCKED`
- `UNKNOWN`

Display labels such as `VERY HIGH` are normalized to `VERY_HIGH`.

## Target distribution

Holdout v1 was strongly concentrated in `VERY_HIGH` cases. Holdout v2 should
include meaningful representation from every applicable confidence level,
especially `LOW`, `WEAK`, `VERY_WEAK`, and `BLOCKED`.

No case should be selected merely to improve an aggregate metric.

## Required metrics

- E2E completion rate
- Strict supported recall
- Claim precision
- Unsafe presentation rate
- Safe claim coverage
- Abstention precision
- Abstention recall
- False-WHY
- Confidence-stratified claim precision
- Confidence-stratified supported recall

## WITHHELD reason guidance

A claim annotation may include the optional `withheld_reason` field only when
its `status` is `WITHHELD`. Existing annotations without this field remain
valid.

Allowed reason identifiers:

- `INSUFFICIENT_EVIDENCE`: related evidence exists, but it does not safely
  establish the claim.
- `CONFLICTING_EVIDENCE`: the captured analysis artifact contains an actual
  contradiction or inconsistency.
- `NOT_OBSERVED`: the required evidence was not found within the analyzed
  range. This does not mean that the claim is false or `UNSUPPORTED`.
- `OUTSIDE_SUPPORTED_SCOPE`: the claim type is outside the semantic structures
  currently supported by the analyzer.

Annotation rules:

- Select a reason only from evidence directly observable in the captured
  execution artifact.
- Do not derive `withheld_reason` from the Ground Truth label.
- Do not treat `WITHHELD` as equivalent to a false or `UNSUPPORTED` claim.
- Do not use `NOT_OBSERVED` as evidence that a claim is incorrect.
- Do not infer `CONFLICTING_EVIDENCE` from a commit message or PR title alone.
- Do not add `withheld_reason` to `PRESENTED` or any other non-`WITHHELD`
  status.
- Do not backfill existing annotations by guessing a reason.

The example in `SCORING_TEMPLATE.json` demonstrates the field shape only.
Real annotations must use evidence from their own preserved execution output.

## Evaluation boundary

Holdout v1 remains frozen. Holdout v2 cases, results, and annotations must be
stored only under `benchmark/holdout_v2`.
