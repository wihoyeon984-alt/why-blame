# Changelog

All notable changes to Why-Blame are documented in this file.

## [0.3.3] - 2026-10-16

### Changed

- 실제 릴리스 변경 요약

### Validation

- Full verification passes.
- HTTP ResourceWarning count is zero.
- Holdout v1 integrity verification passes.
- Holdout v2 post-improvement scoring passes.
## [0.3.2] - 2026-10-16

### Changed

- Add verified release automation and include the changelog in source distributions

### Validation

- Full verification passes.
- HTTP ResourceWarning count is zero.
- Holdout v1 integrity verification passes.
- Holdout v2 post-improvement scoring passes.
## [0.3.1] - 2026-10-16

### Fixed

- Closes consumed GitHub HTTP error response streams after
  reading their response bodies.
- Removes HTTPError 403, 404, and 429 ResourceWarning
  messages during test cleanup.
- Preserves the existing conservative GitHub HTTP error
  classification behavior.

### Validation

- 374 unit tests pass.
- HTTP ResourceWarning count is zero.
- GitHub Actions passes on Windows and Ubuntu with Python
  3.9, 3.11, and 3.14.
## [0.3.0] - 2026-10-16

### Added

- A canonical SHA-256 integrity baseline for Holdout v1.
- A reproducible Holdout v2 evaluation framework with case,
  candidate, annotation, confidence, dataset, loader,
  validation, metric, report, and scoring components.
- Ten frozen Holdout v2 Ground Truth cases with first-run
  outputs, metadata, and annotations.
- Confidence-stratified claim precision, supported recall,
  total presentation, and unsafe presentation metrics.
- A separately preserved post-improvement evaluation and
  comparison scorer.
- Cross-platform artifact integrity validation for Windows
  and Linux.

### Improved

- Safely preserves directly verified behavior under limited
  or inconsistent evidence.
- Recovers the conditional fp.read() to RequestField data
  flow in requests_003.
- Recovers non-tuple traversal and child-node append behavior
  in rich_001.
- Recovers per-line tab-position initialization behavior in
  rich_002.
- Makes Holdout v1 integrity verification independent of the
  current working directory.
- Canonicalizes text artifact hashes across CRLF and LF
  checkouts.

### Evaluation

Official frozen first-run baseline:

- Claim precision: 1.000
- Supported recall: 0.850
- Unsafe presentation rate: 0.000

Post-improvement evaluation:

- Claim precision: 1.000
- Supported recall: 1.000
- Unsafe presentation rate: 0.000
- Supported presentations recovered: 3
- Unsafe presentations added: 0

### Validation

- 374 unit tests pass.
- GitHub Actions passes on Windows and Ubuntu with Python
  3.9, 3.11, and 3.14.

## [0.2.4] - 2026-10-12

- Previous stable release.
