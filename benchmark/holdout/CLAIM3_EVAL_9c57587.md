# Recursive Fallback Claim Recovery Evaluation

## Evaluation scope

- Branch: claim-recovery-v1
- Guarded helper extraction commit: 8e67df7
- Recursive fallback extraction commit: 9c57587
- Holdout cases: 10
- Ground-truth claims: 55
- Supported claims: 32
- Required abstentions: 23
- Unit tests: 277/277 passed
- Holdout execution: 10/10 completed

## Recovered claim

The following supported claim changed from MISSED to PRESENTED:

- pytest_001 / claim_003
  - The output presents that `_imp_fix_co_filename` is used when available.
  - The output presents that `_replace_code_filenames` is used as a
    Pure-Python recursive fallback.

The fallback classification requires all of the following direct evidence:

- The directly analyzed helper returns the local fallback helper.
- The fallback helper docstring explicitly identifies a Pure-Python fallback.
- The fallback helper AST contains a recursive self-call.

Ordinary nested helpers and unknown calls remain unexpanded.

## Metric comparison

| Metric | Original | Limited narrative | Recursive fallback |
| --- | ---: | ---: | ---: |
| Presented claims | 25 | 27 | 28 |
| Strict supported recall | 0.781 | 0.844 | 0.875 |
| Observed supported recall | 0.781 | 0.844 | 0.875 |
| Safe claim coverage | 0.455 | 0.491 | 0.509 |
| E2E completion | 1.000 | 1.000 | 1.000 |
| Abstention precision | 1.000 | 1.000 | 1.000 |
| Unsafe presented | 0 | 0 | 0 |
| False-WHY | 0 | 0 | 0 |

## Safety conclusion

The implementation recovered one additional directly supported behavior
claim without increasing unsafe presentations or False-WHY output.

The implementation does not classify a helper as a recursive Python fallback
from its name alone. The return relationship, explicit fallback documentation,
and recursive AST structure must all be present.

## Evaluation note

The frozen ground truth and original baseline directories were not modified.

The claim3 evaluation reused the previous two reviewed annotations and changed
only `pytest_001 / claim_003` from MISSED to PRESENTED.
