# SIA Audit Manifest

## Upstream artifact audited

Repository: casys-kaist/sia  
Branch: main  
Pinned commit: 7645a9c644db55d677c814687db8bae87f719b9d

This commit is the exact public artifact snapshot used for the reproducibility audit.

## Verified artifact defects

The automated audit detected six reproducibility defects in the pinned snapshot:

1. bench.cpp parses --bg but constructs SIndex with a hard-coded background worker count of 1.
2. --ideal-training-time falls through to default: abort() because case 'z' lacks break.
3. scripts/lazy_delete.py loops over 5/30/100/300 seconds but does not pass training_time to the executable.
4. scripts/node_size.py labels Twitter runs with different node_accuracy values but does not pass the corresponding SIndex error-bound arguments.
5. CMake target blocks for original/sia-sw/ideal benchmark binaries are commented out.
6. README documents a microbenchmark executable name that does not match the CMake target naming.

## Fix validation

A narrow patch was applied without changing the core index algorithm.

Validation on GitHub Actions:
- pristine snapshot: 6/6 defects detected
- patched snapshot: 0/6 of the targeted defects detected
- micro_ideal_UNIFORM_DIST: built successfully
- --ideal-training-time=5: smoke test ran successfully

## Scope of the claim

This audit supports the following statement:

> The pinned public SIA artifact contains verified reproducibility defects in its released benchmark scripts/build configuration.

It does NOT support either of these statements:

- that the paper's original measurements are wrong;
- that the authors used the same broken public paths to generate the paper's reported numbers.

Numerical replication results collected on GitHub-hosted runners are retained only as exploratory evidence because the hardware does not match the paper's evaluation platform and the benchmark exhibits run-to-run variance.

## Next research direction

Treat the reusable automated audit as the primary output. Apply equivalent checks to additional learned-index research artifacts to determine whether these defect classes are isolated or systematic.
