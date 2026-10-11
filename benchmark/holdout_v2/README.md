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

## Evaluation boundary

Holdout v1 remains frozen. Holdout v2 cases, results, and annotations must be
stored only under `benchmark/holdout_v2`.
