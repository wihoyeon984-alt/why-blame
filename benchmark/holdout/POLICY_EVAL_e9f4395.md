# Limited Narrative Policy Evaluation

## Evaluation scope

- Branch: claim-recovery-v1
- Policy implementation commit: bdf8ffb
- Integration test commit: e9f4395
- Holdout cases: 10
- Ground-truth claims: 55
- Supported claims: 32
- Required abstentions: 23
- Unit tests: 275/275 passed
- Holdout execution: 10/10 completed

## Policy change

Low- or weak-confidence narratives continue to abstain from asserting a
specific change reason.

A behavior claim may be presented conservatively only when all of the
following conditions hold:

- The claim status is SUPPORTED.
- The claim type is BEHAVIOR.
- The claim is target-relevant.
- Supporting DIFF evidence is present.
- Structured semantics are present.
- Semantic safety evaluates to SAFE_TO_RENDER.

Blocked, conflicting, unverified, and ordinary low-confidence claims remain
hidden.

## Reannotated claims

Only the following supported claims changed from MISSED to PRESENTED:

- pytest_001 / claim_002
  - The output presents that the original code object is returned when
    `co.co_filename == filename`.

- urllib3_001 / claim_002
  - The output presents that `sockets.append(sock)` occurs before
    `sock.bind((host, port))`.
  - The output retains WEAK confidence and does not assert a concrete change
    reason.

All other annotations were preserved.

## Metric comparison

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Presented claims | 25 | 27 | +2 |
| Strict supported recall | 0.781 | 0.844 | +0.063 |
| Observed supported recall | 0.781 | 0.844 | +0.063 |
| Safe claim coverage | 0.455 | 0.491 | +0.036 |
| E2E completion | 1.000 | 1.000 | unchanged |
| Abstention precision | 1.000 | 1.000 | unchanged |
| Unsafe presented | 0 | 0 | unchanged |
| False-WHY | 0 | 0 | unchanged |

## Safety conclusion

The policy recovered two directly supported behavior claims without
increasing unsafe presentations or False-WHY output.

Specific change reasons remain withheld when external evidence is
insufficient.

## Evaluation note

The frozen case metadata retains its original implementation commit. This
evaluation used the frozen ground truth with outputs generated from the
policy implementation and integration-test commits listed above.

The two recovered claims were manually reannotated against the new output.
The original current_run and current_scoring baseline directories were not
modified.
