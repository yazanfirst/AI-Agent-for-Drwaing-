# Research Artifact Auditor — Prototype v0.1

Purpose: statically detect mechanically-checkable experiment wiring problems
before attempting expensive numerical reproduction.

This prototype intentionally does **not** claim that a paper is wrong.

## Checks

1. **SWEEP_VALUE_NOT_PROPAGATED (HIGH)**  
   A Python experiment loop varies a declared sweep variable, and that variable
   appears in output naming/labeling but not in the command executed before
   shell redirection.

2. **CLI_CASE_FALLTHROUGH_TO_DEFAULT (HIGH)**  
   A C/C++ CLI switch case parses a value and falls directly into `default:`
   without break/return/throw.

3. **CLI_VALUE_PARSED_BUT_UNUSED (MEDIUM)**  
   A getopt-style CLI value is parsed into a variable that appears only in its
   declaration and parser assignment in the same translation unit. This is a
   heuristic and requires human confirmation.

4. **SINGLE_REPEAT_EXPERIMENT (INFO)**  
   An experiment-like Python script sets a repeat/trial/run count to 1. This is
   methodological metadata, not a defect by itself.

## Validation set

Pinned snapshots:

- SIA: `casys-kaist/sia@7645a9c644db55d677c814687db8bae87f719b9d`
- ALEX: `microsoft/ALEX@4370da6aa8b509fdc9b0d2c49faa0624b0078589`
- PGM-index: `gvinciguerra/PGM-index@c6fcf3d34e55eb0061b01e2f49dfcbdb711f1407`
- RadixSpline: `learnedsystems/RadixSpline@ab96aa59d429e7423beba2350bdcdf88952df282`

SIA is the known positive case. The others are controls: they are benchmark/
library repositories and should not be treated as full paper-reproduction
artifacts merely because they contain benchmark code.

The next criterion is precision: if the prototype flags high-confidence
defects in controls without a real wiring problem, the rule must be narrowed
before expanding the dataset.


## Current validation status

The prototype has two independently verified positive cases:

- **SIA**: experiment sweep/CLI wiring defects.
- **BASIL**: broken reproduction-document command paths.

It has also been run against ten pinned control repositories with zero
HIGH-confidence findings:

ALEX, PGM-index, RadixSpline, SOSD, RMI, LearnedSecondaryIndex, LIPP, DILI, APEX, and CARMI.

See `VALIDATION_REPORT.md` for exact commit hashes, findings, scope, and the
current research gate.

## Documentation consistency rule

The auditor now checks project-facing README/reproduction/artifact/experiment
Markdown files for relative `.sh` and `.py` commands that do not exist.
It tracks simple working-directory changes inside shell code blocks, including:

```bash
git clone https://github.com/org/repo.git
cd repo
./scripts/run.sh
```

This was added only after BASIL exposed documentation drift, and it was
revalidated against the existing control set to avoid known false positives.
