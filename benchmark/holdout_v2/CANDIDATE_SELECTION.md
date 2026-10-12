# Holdout v2 Candidate Selection Protocol

This document freezes the selection rules used to construct Holdout v2 before
any candidate is scored.

## Purpose

Holdout v2 expands evaluation coverage without modifying Holdout v1 or selecting
cases based on favorable system output.

## Eligibility

A candidate case must:

- reference a public repository;
- pin an immutable commit SHA;
- identify a concrete file and line range;
- contain enough public history for independent annotation;
- define Ground Truth claims before system execution;
- avoid overlap with Holdout v1 cases;
- avoid using generated system output to define Ground Truth.

## Exclusions

Exclude a candidate when:

- the pinned commit cannot be retrieved;
- the relevant file does not exist at the pinned commit;
- the history is unavailable or legally restricted;
- the Ground Truth depends on private information;
- the case duplicates an existing evaluation case;
- the case was selected because the system already performed well on it.

## Target coverage

Candidate selection should include:

- direct behavior claims;
- unsupported causal claims requiring abstention;
- ambiguous evidence;
- conflicting or revert-related evidence;
- helper-call and fallback behavior;
- statement-ordering behavior;
- rename, move, revert, and merge history where available;
- low-confidence and blocked outcomes.

## Confidence distribution

Holdout v1 was concentrated in VERY_HIGH outcomes. Holdout v2 should increase
representation of:

- MEDIUM
- LOW
- WEAK
- VERY_WEAK
- BLOCKED

Confidence is recorded after execution. It must not be used to retroactively
remove an eligible case.

## Freeze procedure

For every accepted case:

1. Pin the repository URL and commit SHA.
2. Define the target file and line range.
3. Write all Ground Truth claims.
4. Assign each Ground Truth label.
5. Review Claim IDs for uniqueness.
6. Mark the case as frozen.
7. Commit the case definition.
8. Only then execute the system.
9. Store the raw result without replacement.
10. Annotate every Ground Truth Claim.

## Reporting

Report execution reliability separately from semantic performance.

Required aggregate metrics include:

- E2E completion rate;
- strict supported recall;
- claim precision;
- unsafe presentation rate;
- safe claim coverage;
- abstention precision and recall;
- False-WHY count;
- confidence-stratified precision and recall.

All excluded or failed candidates should remain documented with the exclusion
or failure reason.
