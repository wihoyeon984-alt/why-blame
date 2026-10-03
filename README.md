# why-blame

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

Both evaluations have complete annotations:

```text
First-run: 55 / 55 claims
Current:   55 / 55 claims
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

Seven SUPPORTED claims remain unrecovered in Holdout v1.

### Bounded semantic scope expansion

- `aiohttp_003 / claim_002`
- `django_001 / claim_003`
- `pytest_001 / claim_002`
- `pytest_001 / claim_003`

### Semantic-detail recovery

- `sqlalchemy_001 / claim_002`
- `sqlalchemy_001 / claim_003`

### Ordering and control-flow semantics

- `urllib3_001 / claim_002`

## Testing

The project currently passes `226 / 226` tests.

The Holdout scorer-specific suite passes `18 / 18` tests.

## Development Policy

Future semantic changes should be motivated by repeated observable failures rather than repository-specific benchmark rules.

The preferred loop is: observe failure -> identify a reusable failure class -> write a synthetic regression test -> implement a bounded change -> run the full regression suite -> re-score the frozen Holdout -> check recovery and safety together.

Recall improvements should not be accepted by themselves if they increase unsupported explanations.

## Project Principle

> **Explain what the available evidence can support, and stop where the evidence stops.**

> **Related is not the same as proven.**
