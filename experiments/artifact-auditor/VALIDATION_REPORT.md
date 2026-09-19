# Artifact Auditor — Validation Report

Date: 2026-09-19

## Goal

Test whether a conservative static auditor can detect mechanically verifiable
reproducibility defects in research artifacts without claiming that the papers'
reported numerical results are wrong.

The validation strategy deliberately includes:
- known positive artifacts with manually verified defects;
- control repositories where HIGH-confidence findings should remain zero.

## Auditor rules currently implemented

### HIGH confidence

1. **SWEEP_VALUE_NOT_PROPAGATED**  
   A declared experiment sweep variable changes output naming/labels but does
   not reach the executed command.

2. **CLI_CASE_FALLTHROUGH_TO_DEFAULT**  
   A C/C++ CLI switch case parses an option and falls into `default:` without
   break/return/throw.

3. **DOCUMENTED_COMMAND_PATH_MISSING**  
   Project-facing reproduction documentation tells the user to execute a
   relative `.sh` or `.py` path that does not exist at the documented
   working directory. The checker tracks simple `cd` transitions and
   `git clone ...; cd <repo>` flows inside fenced shell blocks.

### MEDIUM confidence

4. **CLI_VALUE_PARSED_BUT_UNUSED**  
   A getopt-style CLI value appears to be parsed into a variable with no
   meaningful use in the same translation unit. This is a heuristic and
   requires human review.

### INFO only

5. **SINGLE_REPEAT_EXPERIMENT**  
   An experiment-like Python script explicitly sets its repeat/trial/run count
   to one. This is methodological metadata, not a defect by itself.

## Positive case 1 — SIA

Pinned snapshot:

`casys-kaist/sia@7645a9c644db55d677c814687db8bae87f719b9d`

Generic auditor HIGH findings:

1. `scripts/lazy_delete.py` — `training_time` is swept over
   5/30/100/300 but is not propagated into the benchmark command.
2. `scripts/node_size.py` — the Twitter node-accuracy sweep changes
   filenames/labels but does not pass the corresponding error-bound settings
   to the executable.
3. `bench.cpp` — `--ideal-training-time` parses a value and then falls
   through into `default: abort()`.

Validation result:

- HIGH: 3
- MEDIUM: 7
- INFO: 5
- validation gate: PASS

A separate SIA-specific audit also verified additional artifact defects that
are not yet generalized into the generic auditor, including the hard-coded
background-worker count, disabled CMake target blocks, and a README/target
name mismatch.

## Positive case 2 — BASIL

Pinned snapshot:

`DKU-StarLab/BASIL@cc600dde8dd5019328d7a4a07dfc7dd51258648f`

The auditor found 8 broken documentation references corresponding to 7 unique
missing command paths in project-facing reproduction documentation:

1. `./scripts/download_data.sh`
   - referenced in both `README.md` and `reproduce.md`
   - the repository instead contains `./scripts/download.sh`

2. `./scripts/reproduce/reproduce_perf.sh`
   - referenced by `reproduce.md`
   - no such file exists in the pinned tree

3. `./scripts/graphs/fig6_sampling_impact_srmi.py`
   - missing; the tree contains `fig6_sampling_impact_rmi.py`

4. `./scripts/graphs/fig7_sampling_impact_spgm.py`
   - missing; the tree contains `fig7_sampling_impact_pgm.py`

5. `./scripts/graphs/fig8_sampling_impact_srs.py`
   - missing; the tree contains `fig8_sampling_impact_rs.py`

6. `./scripts/graphs/fig9_sampling_impact_scht.py`
   - missing; the tree contains `fig9_sampling_impact_cht.py`

7. `./scripts/graphs/fig5_hardness.py`
   - missing; the tree contains `fig5_dataset.py`

Strict BASIL validation requires all seven unique paths to be found and rejects
any unexpected HIGH documentation finding.

Validation gate: PASS.

## Control repositories

Pinned snapshots with zero HIGH findings:

| Repository | Commit | HIGH |
|---|---|---:|
| Microsoft ALEX | 4370da6aa8b509fdc9b0d2c49faa0624b0078589 | 0 |
| PGM-index | c6fcf3d34e55eb0061b01e2f49dfcbdb711f1407 | 0 |
| RadixSpline | ab96aa59d429e7423beba2350bdcdf88952df282 | 0 |
| SOSD | f52f4cba01dfcd37f1574551fccef00198863b88 | 0 |
| RMI | 6f03e69cfa73979d52c589c86ece0b6d37c69330 | 0 |
| LearnedSecondaryIndex | 02da12bab5f48b8b9864d6bee6134d066abc0516 | 0 |
| LIPP | fe6ca4954f00875482f9e4dd63b34dae2384d23b | 0 |
| DILI | babd1a2c53df841b55bc5867a6925ccc6fe88d87 | 0 |
| APEX | 5aee22aa6a6059e161aa2aca6e4080118aa246e9 | 0 |
| CARMI | 2911ee504d084a0bc30bafe5f2732564a3fad893 | 0 |

This is an initial precision check, not a statistical estimate of false
positive rate.

## What this demonstrates

The prototype is no longer a SIA-specific checker.

It has now detected two different defect classes in two independent research
artifacts:

- **experiment parameter wiring defects** in SIA;
- **reproduction documentation/path drift** in BASIL.

At the same time, the HIGH-confidence rules produced zero HIGH findings across
ten control repositories in the pinned validation set.

## What this does NOT demonstrate

This report does not establish:

- that any paper's published numerical results are wrong;
- that these defect classes are common across the learned-index literature;
- a measured false-positive or false-negative rate;
- publication-grade artifact reproducibility.

The current result is a validated proof of concept.

## Next gate

Expand the corpus with more explicit paper-reproduction artifacts, not merely
libraries. The project becomes substantially more research-worthy only if the
auditor continues to discover independently verified defect classes with low
false-positive rates across a larger corpus.
