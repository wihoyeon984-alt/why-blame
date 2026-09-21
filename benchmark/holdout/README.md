\# Why-Blame Holdout Benchmark v1



\## Purpose



This benchmark evaluates whether why-blame generalizes to previously unseen

open-source history cases.



The existing pilot cases are development cases and MUST NOT be treated as

holdout data.



Development set:



\- requests\_001

\- requests\_002

\- flask\_001

\- click\_001

\- click\_002



The Holdout Benchmark must use new cases that were not used to design or tune

the Claim Recovery pipeline.



\---



\## Core Rule



Ground Truth must be frozen before running why-blame on a holdout case.



Required order:



1\. Select an OSS repository and target.

2\. Freeze the repository revision.

3\. Inspect Git history, diff, commit metadata, PR, and Issue evidence.

4\. Write Ground Truth.

5\. Map each Ground Truth Claim to its supporting evidence.

6\. Mark the case as frozen.

7\. Only then run why-blame.

8\. Record the first result.

9\. Do not modify the implementation based on an individual holdout result.



A holdout case becomes development data if its result is used to tune the

implementation.



\---



\## Holdout Size



Target for v1:



\- 10 cases

\- at least 5 repositories

\- multiple history shapes

\- multiple evidence sufficiency levels



No repository should dominate the benchmark.



\---



\## Desired Case Diversity



The benchmark should attempt to include examples of:



1\. Direct behavior

2\. Lexical similarity trap

3\. Negation

4\. Contradicting evidence

5\. Historical pollution

6\. Partial evidence

7\. Conditional behavior

8\. Unrelated PR or Issue evidence

9\. Genuine ambiguity

10\. No sufficient explanation



These are diversity goals, not labels that should be forced onto a selected

repository.



Cases must be chosen from real evidence first.



\---



\## Claim Types



Ground Truth Claims may use:



\- BEHAVIOR

\- CAUSE

\- REVERT\_FACT

\- REVERT\_CAUSE



CAUSE and REVERT\_CAUSE require stronger evidence than observable behavior.



\---



\## Claim Labels



Each Ground Truth Claim must have one of:



\- SUPPORTED

\- UNSUPPORTED

\- AMBIGUOUS

\- CONFLICTING



Definitions:



SUPPORTED:

The frozen public evidence sufficiently supports the Claim.



UNSUPPORTED:

The Claim may sound plausible but is not supported by the frozen evidence.



AMBIGUOUS:

Relevant evidence exists, but the Claim cannot be established safely.



CONFLICTING:

Available evidence explicitly points in incompatible semantic directions.



\---



\## Structured Claim Fields



Where applicable, a Claim should be decomposed into:



\- action

\- subject

\- target

\- condition

\- scope



Do not invent a field merely to make the Claim structurally complete.



Unknown fields should remain empty.



\---



\## Entailment Levels



Each populated semantic field should be assigned one of:



\- DIRECT

\- PARTIAL

\- INFERRED

\- NONE

\- CONFLICTING



DIRECT means the frozen evidence explicitly supports that semantic field.



Token overlap alone is not DIRECT entailment.



Identifier similarity alone is not DIRECT entailment.



Absence of contradiction is not evidence of support.



\---



\## Evidence Attribution



Each Claim must identify which evidence supports it.



Possible channels include:



\- DIFF

\- COMMIT

\- PR

\- ISSUE

\- REVERT

\- HISTORY



Each attribution should include a stable reference when possible:



\- commit SHA

\- PR number

\- Issue number

\- relevant diff expression or line range



Evidence relevance and Evidence sufficiency are separate concepts.



Relevant evidence may still be insufficient.



\---



\## Frozen Ground Truth



A case is frozen only when:



ground\_truth\_frozen: true



Once frozen, Ground Truth must not be edited merely because why-blame produces

a different answer.



If the Ground Truth itself is later found objectively incorrect, the change

must be documented separately rather than silently rewritten.



\---



\## First-Run Rule



The first why-blame result after Ground Truth freeze is the official Holdout

v1 result for that case.



Save it before any implementation change.



\---



\## No-Tuning Rule



During the official Holdout v1 run:



\- Do not add a special parser for a failed case.

\- Do not add repository-specific rules.

\- Do not weaken a safety policy to improve Recall.

\- Do not rewrite Ground Truth to match system output.

\- Do not rerun after code changes and replace the first result.



Failures are benchmark results.



\---



\## Metrics



\### Claim Precision



Correctly recovered supported claims

/

All claims presented by the system



\### Supported Claim Recall



Recovered supported Ground Truth claims

/

All supported Ground Truth claims



\### Unsupported Claim Rate



Unsupported claims presented

/

All claims presented by the system



\### Case-level False-WHY Rate



Cases containing at least one unsupported WHY

/

All evaluated cases



\### Evidence Attribution Accuracy



Presented claims with correct supporting evidence attribution

/

Presented claims requiring attribution



\### Abstention Precision



Correct abstentions

/

All system abstentions



\### Abstention Recall



Correct abstentions

/

All Ground Truth situations requiring abstention



\---



\## Safety Interpretation



For why-blame, abstention is not automatically a failure.



Expected safe outcomes include:



\- insufficient evidence -> abstain

\- semantic entailment is PARTIAL -> abstain from stronger Claim

\- semantic entailment is INFERRED -> abstain from DIRECT Claim

\- contradiction exists -> block the Claim

\- evidence is unavailable -> do not claim absence

\- related PR exists but does not prove the Claim -> do not strengthen



The benchmark must therefore measure both explanation ability and correct

abstention.



\---



\## Architecture Principle



The Holdout evaluates the following intended pipeline:



Target-aware history

\-> candidate discovery

\-> structured syntax

\-> structured semantics

\-> evidence mapping

\-> field-level entailment

\-> contradiction check

\-> semantic safety

\-> safe rendering



Important:



Predicate Delta is semantic evidence about how code changed.



Predicate Delta is not itself an explanation of why the change was made.



Token overlap is an evidence-discovery signal.



Token overlap is not semantic proof.



NO\_CONTRADICTION is not equivalent to SUPPORTED.



\---



\## Reporting



The final Holdout v1 report should include:



\- number of repositories

\- number of cases

\- number of Ground Truth Claims

\- Claim Precision

\- Supported Claim Recall

\- Unsupported Claim Rate

\- Case-level False-WHY Rate

\- Evidence Attribution Accuracy

\- Abstention Precision

\- Abstention Recall



Also report failures individually.



Aggregate numbers must not hide semantic overclaim failures.

