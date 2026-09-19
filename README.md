# Research Artifact Auditor

A conservative static-analysis prototype for finding mechanically verifiable
reproducibility defects in research-code artifacts.

## What this repository contains

This clean branch contains only the research work from the current project:

- `experiments/artifact-auditor/`
  - generic auditor prototype
  - validation methodology
  - validation report across learned-index repositories
- `experiments/sia-artifact-audit/`
  - pinned SIA audit
  - verified artifact defects
  - narrow fixes and upstream issue draft
- `.github/workflows/`
  - automated validation workflows for the auditor and SIA audit

Obsolete exploratory performance experiments and unrelated drawing/DXF data
were intentionally removed from this branch.

## Current result

The generic auditor has two independently verified positive cases:

- **SIA** — experiment sweep / CLI wiring defects
- **BASIL** — broken reproduction-document command paths

It has also been tested on a control corpus including ALEX, PGM-index,
RadixSpline, SOSD, RMI, LearnedSecondaryIndex, LIPP, DILI, APEX, and CARMI
without HIGH-confidence findings in those pinned snapshots.

See:

- `experiments/artifact-auditor/VALIDATION_REPORT.md`
- `experiments/artifact-auditor/README.md`
- `experiments/sia-artifact-audit/AUDIT_MANIFEST.md`

## Scope

This project audits public research artifacts. It does **not** claim that a
paper's published numerical results are wrong merely because its public
artifact contains reproducibility defects.
