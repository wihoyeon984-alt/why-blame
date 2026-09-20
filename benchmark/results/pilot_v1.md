# why-blame OSS Benchmark: Pilot v1

## Status

Pilot baseline completed before claim-recovery improvements.

This document records the initial real-world OSS benchmark result for why-blame.

The purpose of this pilot is not to claim statistically meaningful performance, but to establish a reproducible baseline before changing the Narrative or Evidence recovery logic.

The Ground Truth for each case was frozen before running why-blame.

---

## Benchmark Scope

Repositories:

- psf/requests
- pallets/flask
- pallets/click

Cases:

- requests_001
- requests_002
- flask_001
- click_001
- click_002

Total:

- Repositories: 3
- OSS Cases: 5
- Ground Truth Supported Claims: 10

---

## Evaluation Principles

The benchmark distinguishes between three types of claims.

### Supported Claim

A claim directly supported by available Git, Diff, PR, Issue, or other verified repository evidence.

### Unsupported Claim

A claim that the system presents as a reason or fact even though the available evidence does not support it.

### Ambiguous Claim

A claim that may be plausible but cannot be established from the available evidence with sufficient confidence.

Ground Truth is written before executing why-blame and is not changed to match system output.

---

## Primary Metrics

### Supported Claim Recall

Measures how many Ground Truth supported WHY claims are explicitly recovered by why-blame.

Formula:

```text
Supported Claim Recall
= Recovered Supported Claims / Ground Truth Supported Claims
```

### False-WHY Rate

Measures the proportion of benchmark cases in which why-blame asserts a specific unsupported change reason as if it were established fact.

Formula:

```text
False-WHY Rate
= False-WHY Cases / Evaluated Cases
```

### Unsupported Claim Count

Counts explicit system claims that are not supported by the frozen Ground Truth Evidence.

---

# Results

## Case 1: requests_001

Repository:

```text
psf/requests
```

Target:

```text
src/requests/adapters.py:99-100
```

Scenario:

```text
Custom SSLContext / HTTPAdapter compatibility
```

Ground Truth:

- Existing custom SSLContext configuration should not be replaced by the default preloaded SSLContext.
- The change addresses compatibility with custom SSLContext configuration used through HTTPAdapter / PoolManager.

System result:

```text
Evidence Coverage:       100%
Consistency:             HIGH
Confidence:              VERY HIGH
False-WHY:               false
Ground Truth Claims:     2
Recovered WHY Claims:    0
Supported Claim Recall:  0%
```

Observed behavior:

- why-blame correctly detected the relevant PR.
- Nearby performance-related history was not incorrectly attributed as the direct reason for the target change.
- No unsupported performance, security, customer-request, or memory-related WHY was generated.
- The Narrative did not explicitly recover the supported custom SSLContext rationale even though Commit, Diff, and PR Evidence were available.

Assessment:

```text
SAFE BUT CONSERVATIVE
```

---

## Case 2: requests_002

Repository:

```text
psf/requests
```

Target:

```text
src/requests/utils.py:137-138
```

Scenario:

```text
Unicode string Content-Length / encoded byte length
```

Ground Truth:

- super_len should measure the encoded byte length of a string rather than its Unicode character count.
- String inputs are encoded as UTF-8 before their length is calculated.

System result:

```text
Evidence Coverage:       100%
Consistency:             HIGH
Confidence:              VERY HIGH
False-WHY:               false
Ground Truth Claims:     2
Recovered WHY Claims:    0
Supported Claim Recall:  0%
```

Observed behavior:

- why-blame correctly detected PR #6589.
- Commit and PR metadata exposed the encoded-byte rationale.
- No unsupported performance, security, AWS-specific, or memory-related causal claim was generated.
- The Narrative stopped at identifying the Commit and linked PR instead of explicitly explaining the supported encoded-byte and UTF-8 rationale.

Assessment:

```text
SAFE BUT CONSERVATIVE
```

---

## Case 3: flask_001

Repository:

```text
pallets/flask
```

Target:

```text
src/flask/testing.py:243-244
```

Scenario:

```text
Preserved request context ordering /
follow_redirects final session state
```

Ground Truth:

- Preserved request contexts must be restored in the correct order so that the final request context is not obscured by an earlier one.
- The change fixes the final session state observed by the Flask test client when follow_redirects is used.

System result:

```text
Evidence Coverage:       100%
Consistency:             HIGH
Confidence:              VERY HIGH
False-WHY:               false
Ground Truth Claims:     2
Recovered WHY Claims:    0
Supported Claim Recall:  0%
```

Observed behavior:

- why-blame correctly detected the implementation PR #5797.
- The change history exposed the preserved-context ordering change.
- No unsupported claim about production HTTP sessions, performance, security, or browser cookie handling was generated.
- The Narrative did not explicitly explain why context ordering matters or connect the change to the final session state when redirects are followed.

Assessment:

```text
SAFE BUT CONSERVATIVE
```

---

## Case 4: click_001

Repository:

```text
pallets/click
```

Target:

```text
src/click/core.py:1560-1561
```

Scenario:

```text
KeyboardInterrupt race handling in Command.main()
```

Ground Truth:

- A late KeyboardInterrupt during Command.main error, abort, or exit handling should not escape as an unhandled traceback.
- Once Command.main has determined the intended exit code, a late KeyboardInterrupt should not replace that exit result.

System result:

```text
Evidence Coverage:       100%
Consistency:             HIGH
Confidence:              VERY HIGH
False-WHY:               false
Ground Truth Claims:     2
Recovered WHY Claims:    0
Supported Claim Recall:  0%
```

Observed behavior:

- why-blame correctly detected PR #3818.
- The Commit and PR exposed the KeyboardInterrupt race-condition topic.
- No unsupported claim about performance, security, Windows-specific behavior, or ignoring every KeyboardInterrupt was generated.
- The Narrative did not explicitly recover that a late interrupt should not escape as an unhandled traceback or replace the already determined exit result.

Assessment:

```text
SAFE BUT CONSERVATIVE
```

---

## Case 5: click_002

Repository:

```text
pallets/click
```

Target:

```text
src/click/core.py:2900-2901
```

Scenario:

```text
Original change followed by explicit Revert
```

Ground Truth:

- The original Commit changed default=True sentinel handling so that it applied only to non-boolean flags.
- A later Commit explicitly reverted the original change and restored the previous self.is_flag condition.
- The public Git history does not establish a specific causal reason for performing the Revert.

System result:

```text
Evidence Coverage:       100%
Consistency:             HIGH
Ambiguity:               COMPLEX
Confidence:              MEDIUM
False-WHY:               false
Ground Truth Claims:     2
Recovered WHY Claims:    1
Supported Claim Recall:  50%
```

Observed behavior:

- why-blame detected the explicit Revert.
- History ambiguity increased because of the rollback.
- Confidence was capped at MEDIUM despite full Evidence Coverage and HIGH Consistency.
- The Narrative explicitly acknowledged the rollback history.
- The system did not invent a specific causal reason for the Revert.
- It did not claim that a bug, compatibility problem, performance problem, or referenced Issue was the reason for the rollback.

Assessment:

```text
REVERT SAFETY PASS
```

---

# Pilot Summary

```text
Repositories:                    3
OSS Cases:                       5

Ground Truth Supported Claims:  10
Recovered Supported Claims:      1

Supported Claim Recall:         10%

Unsupported WHY Claims:          0

False-WHY Cases:                 0
False-WHY Rate:                 0%
```

---

## Additional Revert Evaluation

The Revert case provided an additional test of the Confidence model.

Observed:

```text
Evidence Coverage: 100%
Consistency:       HIGH
Revert:            detected
Ambiguity:         COMPLEX
Confidence:        MEDIUM
```

This matches the intended safety policy:

```text
High Evidence Availability
        +
High Consistency
        +
Rollback History
        ↓
History Ambiguity increases
        ↓
Confidence is capped
        ↓
Narrative becomes conservative
```

Pilot result:

```text
Revert Detection:       PASS
Ambiguity Escalation:   PASS
Confidence Cap:         PASS
Unsupported Cause:      PASS
```

---

## Observed Parser Issue

One possible Git history parsing artifact was observed in `click_002`.

The Timeline displayed Commit:

```text
6c4a77ba24854dab793a8ff72110a0a24c403c9f
```

twice.

One event contained normal metadata, while another appeared with:

```text
Date: Unknown
Message: empty
```

This may indicate duplicate parsing of a `git log -L` history fragment.

This issue is recorded for later investigation.

No parser change was made during Pilot v1 in order to avoid tuning the implementation against a single Benchmark observation.

---

# Main Finding

The first five real-world OSS cases show a consistent initial pattern.

why-blame appears strong at:

- locating relevant Git History,
- detecting relevant Commit changes,
- linking external PR / Issue Evidence,
- avoiding unsupported causal claims,
- preventing False-WHY,
- detecting Reverts,
- increasing ambiguity for rollback History,
- reducing Confidence when History becomes ambiguous.

However, it appears weak at converting sufficiently supported Evidence into explicit WHY claims.

The initial behavior can be summarized as:

```text
High Safety
+
Low Supported Claim Recall
```

or:

```text
Precision-first, recall-poor
```

The current system tends to say:

```text
"This change is linked to PR #123."
```

even when Evidence may support a stronger but still grounded statement about the actual reason for the change.

---

# Interpretation

The Pilot does not suggest that why-blame should become more aggressive in generating explanations.

Instead, it suggests that the system needs a better distinction between:

```text
Evidence relationship
```

and:

```text
Evidence-supported WHY claim
```

For example:

```text
"The final Commit is linked to PR #6589."
```

is an Evidence relationship.

It does not itself explain why the code changed.

A stronger but still Evidence-grounded Claim could be:

```text
"The string is encoded to UTF-8 before its length is calculated so that
the length reflects encoded bytes rather than Unicode character count."
```

Such a Claim should only be emitted when its individual components are supported by verified Evidence.

---

# Important Limitation

This Pilot contains only five manually selected OSS cases across three repositories.

Therefore:

```text
Supported Claim Recall = 10%
False-WHY Rate = 0%
```

must not be interpreted as statistically meaningful estimates of general why-blame performance.

They are baseline observations used to guide development and compare future versions against the exact same frozen Ground Truth.

No broad performance Claim should be made from Pilot v1.

---

# Development Decision

The production algorithm was not changed during Pilot v1 Case collection.

This avoids adapting the implementation to each Benchmark Case while the baseline is still being constructed.

After freezing the five-Case baseline, the next implementation goal is:

> Increase Evidence-supported WHY recovery while preserving the current False-WHY safety behavior.

In other words:

```text
Keep:
Low Unsupported Claim Rate
Low False-WHY Rate

Improve:
Supported Claim Recall
```

The safety boundary should remain:

```text
No direct Evidence
        ↓
No specific causal Claim
```

---

# Next Improvement Direction

The strongest candidate is Claim-level Evidence recovery.

Instead of evaluating only:

```text
Commit
↕
PR
```

the system should eventually evaluate individual Claims.

Example:

```text
Commit
├─ Claim A
├─ Claim B
└─ Claim C

Evidence
├─ supports Claim A
├─ does not verify Claim B
└─ conflicts with Claim C
```

This could allow why-blame to produce output such as:

```text
SUPPORTED

- The change prevents the existing custom SSLContext from being replaced.

  Evidence:
  Commit + Diff + PR

UNVERIFIED

- Performance improvement

  No direct Evidence found.
```

The goal is not to make Narrative more aggressive.

The goal is to make Narrative more informative only when individual Claims are directly supported.

---

# Improvement Safety Requirement

Any future Claim-recovery improvement must preserve the existing False-WHY safeguards.

An improvement should fail evaluation if it increases Recall by introducing unsupported causal Claims.

For example:

```text
Before

Supported Claim Recall: 10%
False-WHY Rate:           0%
```

A future result such as:

```text
Supported Claim Recall: 80%
False-WHY Rate:          30%
```

would not be considered an improvement.

The intended direction is:

```text
Supported Claim Recall ↑

while

Unsupported Claims remain low
False-WHY Rate remains low
```

---

# Frozen Baseline

Pilot v1 is the baseline before Claim-recovery improvements.

Future versions should be evaluated against the same frozen Ground Truth Cases.

Baseline:

```text
Pilot v1

Repositories:           3
OSS Cases:              5
Supported Claims:      10
Recovered Claims:       1

Supported Claim Recall: 10%
False-WHY Rate:          0%

Revert Detection:       PASS
Confidence Cap:         PASS

Observed Parser Issues: 1
```

Future comparison:

```text
Pilot v1
        ↓
Claim-level Evidence improvement
        ↓
Re-run same frozen Benchmark
        ↓
Compare Recall
Compare False-WHY
Compare Unsupported Claims
Compare Confidence behavior
```

---

# Success Criteria for the Next Version

The next version should be considered better than Pilot v1 only if:

1. Supported Claim Recall increases.
2. Unsupported causal Claims remain low.
3. False-WHY safeguards remain effective.
4. Revert ambiguity still reduces Confidence appropriately.
5. Evidence conflicts still block unsupported WHY.
6. Ground Truth remains unchanged during evaluation.

The primary development question after Pilot v1 is therefore:

> Can why-blame recover more of what the Evidence actually supports without starting to claim what the Evidence does not support?

That question defines the next stage of the project.