# Why-Blame Holdout v1 Benchmark Report

## 1. Evaluation Scope

Holdout v1 evaluates Why-Blame on 10 frozen cases selected from public
open-source repositories before the corresponding system runs.

Ground Truth:

- Cases: 10
- Total claims: 55
- SUPPORTED: 32
- UNSUPPORTED: 19
- AMBIGUOUS: 4
- CONFLICTING: 0
- Required abstentions: 23

The original first-run outputs and annotations are preserved separately from
the current-run outputs and annotations.

- `results/`: immutable first-run outputs
- `scoring/`: first-run claim annotations
- `current_run/`: current-system outputs
- `current_scoring/`: current-system claim annotations

The same Ground Truth and scoring formulas are used for both evaluations.

## 2. First-Run vs Current Results

| Metric | First-run | Current | Change |
|---|---:|---:|---:|
| E2E completion | 0.000 | 1.000 | +1.000 |
| Strict supported recall | 0.688 | 0.781 | +0.093 |
| Observed supported recall | 0.688 | 0.781 | +0.093 |
| Unobservable claim rate | 0.000 | 0.000 | 0.000 |
| Safe claim coverage | 0.400 | 0.455 | +0.055 |
| Abstention precision | 0.778 | 1.000 | +0.222 |
| Abstention recall | 0.304 | 0.130 | -0.174 |
| Unsafe presented | 0 | 0 | 0 |

Raw supported-claim recovery:

- First-run supported claims presented: 22 / 32
- Current supported claims presented: 25 / 32

Product reliability:

- First-run completed cases: 0 / 10
- Current completed cases: 10 / 10

Current suppression behavior:

- Correct abstentions: 3
- System abstentions: 3
- WITHHELD claims: 20
- Safe suppressions: 23
- Required abstentions: 23

## 3. Reliability Result

The first Holdout run completed 0 of 10 cases because rendering Unicode
characters could raise `UnicodeEncodeError` on a Windows CP949 console.

The viewer output boundary was changed so characters that cannot be represented
by the active output encoding are safely replaced instead of terminating the
CLI.

The current run completed all 10 Holdout cases.

This reliability change was regression-tested both with a forced CP949 output
stream and through the complete `render_card()` path.

The original failed first-run outputs remain preserved and were not overwritten.

## 4. Semantic Result

Supported-claim recall improved from 22 / 32 to 25 / 32:

- First-run strict supported recall: 0.688
- Current strict supported recall: 0.781

Safe claim coverage also increased:

- First-run: 0.400
- Current: 0.455

No claim annotated as unsafe was presented in either evaluation:

- First-run unsafe presented: 0
- Current unsafe presented: 0

Therefore, the observed recall improvement did not coincide with an increase in
the benchmark's unsafe-presentation count.

## 5. Abstention Trade-off

The current run has a clear abstention trade-off.

Abstention precision increased:

- 0.778 -> 1.000

Abstention recall decreased:

- 0.304 -> 0.130

All 3 explicit current-run abstentions were correct. However, only 3 of the 23
claims requiring abstention were handled through an explicit abstention.

The other unsafe or unsupported claims were primarily suppressed as `WITHHELD`
rather than explicitly described to the user as abstentions.

This means the current system is conservative about presenting unsupported
claims, but often does not explicitly communicate why a claim was suppressed.

Future work should distinguish two separate goals:

1. preventing unsupported explanations from being presented;
2. clearly communicating explicit abstention when evidence is insufficient.

Improving explicit abstention coverage must not come at the cost of increasing
unsafe presentations.

## 6. Remaining Supported-Claim Failures

Seven SUPPORTED claims remain unrecovered in the current evaluation.

### Bounded Semantic Scope Expansion

Four failures require information outside the immediately rendered target
semantics.

- `aiohttp_003 / claim_002`
  - The caller passes `compress=bool(compress)`.
  - The output does not recover the related `WebSocketReader` definition change
    removing the previous compression default.

- `django_001 / claim_003`
  - The target uses `supports_independent_comment_alteration`.
  - The output does not recover the base feature default and the Oracle and
    PostgreSQL backend overrides.

- `pytest_001 / claim_002`
  - The target calls `_fix_code_filename`.
  - The output does not recover the helper behavior that returns the original
    code object when the filename already matches.

- `pytest_001 / claim_003`
  - The target calls `_fix_code_filename`.
  - The output does not recover the helper implementation that selects
    `_imp._fix_co_filename` when available and otherwise uses the fallback
    implementation.

These failures motivate bounded semantic expansion rather than unrestricted
call-graph traversal.

The current experimental foundation allows only direct local helper candidates,
limits expansion depth, and avoids treating attribute calls as local helper
definitions.

Finding a related definition is not sufficient to present a claim. Any expanded
semantic fact must still pass evidence entailment, contradiction checking, and
the safety gate before rendering.

### Semantic Detail Recovery

Two failures remain in `sqlalchemy_001`.

- `claim_002`
  - The output does not present preservation of TEXT / NTEXT collation.

- `claim_003`
  - The output does not present that bounded SQL Server string and character
    types continue deriving reflected length from `max_length`.

These should not be addressed with SQLAlchemy-specific rules. Further work
should first determine whether they represent a reusable semantic extraction
failure class.

### Ordering / Control-Flow Semantics

One remaining failure is `urllib3_001 / claim_002`.

The output presents exception cleanup and its EADDRINUSE retry context but does
not express the important ordering relation:

`socket creation -> append to cleanup collection -> bind attempt`

This indicates a distinction between extracting individual statements and
recovering directly observable ordering or control-flow relations.

## 7. Positive Control

`pydantic_001` remains a useful positive-control case.

Its five SUPPORTED behavior claims are recovered when the necessary semantics
are directly represented in the target diff.

Together with the failures above, this suggests that the observed weakness is
not simply an inability to recover detailed behavior. Failures are concentrated
where explanation requires bounded expansion beyond the immediate target or a
relation between multiple operations.

## 8. Development Policy

Future semantic changes should be justified by repeated observable failures in
the benchmark rather than by individual repository-specific cases.

The intended pipeline remains:

Structured Semantics
-> Evidence Entailment
-> Contradiction Check
-> Safety Gate
-> Safe Rendering

A related symbol, PR, issue, token match, or nearby implementation is not by
itself sufficient evidence for a claim.

The project should preserve the principle:

**Related is not the same as proven.**

## 9. Next Steps

Priority order after this report:

1. Preserve this benchmark comparison as a reproducible checkpoint.
2. Add a repeatable scorer path for current-run annotations.
3. Improve reporting of explicit abstention versus silent safe suppression.
4. Investigate bounded semantic scope expansion using synthetic regression
   tests before Holdout-specific changes.
5. Investigate reusable ordering / control-flow semantic extraction.
6. Re-score Holdout v1 after each generalized change.
7. Add new unseen Holdout cases before substantially expanding semantic
   coverage.

New semantic functionality should not be considered an improvement unless it
either improves measured recovery or safety while preserving the project's
false-WHY constraints.
