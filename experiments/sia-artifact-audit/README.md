# SIA artifact reproducibility audit

This audit targets the current public `casys-kaist/sia` artifact, not the
scientific validity of the PVLDB paper itself.

It checks whether the released scripts and build configuration can execute the
parameter sweeps documented in the repository and paper.

Checks currently covered:

1. `--bg` is parsed but the microbenchmark hard-codes one SIndex background
   worker.
2. `--ideal-training-time` falls through to `default: abort()`.
3. `lazy_delete.py` loops over training intervals but does not pass the
   interval to the executable.
4. The Twitter half of `node_size.py` loops over node accuracy settings but
   does not pass the error-bound arguments.
5. CMake target blocks for original/SIA-SW/ideal are commented out.
6. README's microbenchmark executable name does not match CMake's target name.

The companion guarded fixer is intentionally narrow and makes no algorithmic
changes.
