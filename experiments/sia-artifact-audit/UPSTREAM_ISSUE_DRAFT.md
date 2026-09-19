# Draft upstream issue

## Title

Reproducibility artifact: several benchmark sweep parameters are not applied

## Body

Thanks for releasing the SIA artifact. While trying to reproduce the documented experiments, I found several issues in the current public repository that appear to affect artifact reproducibility.

I want to be precise about scope: **this report is about the currently released artifact/scripts, not a claim that the paper's reported results are incorrect or were generated with these exact broken paths.**

### Confirmed issues on current main

1. **scripts/lazy_delete.py does not pass the training interval**
   - The script loops over `IDEAL_TRAINING_TIME_LIST=(5, 30, 100, 300)`.
   - The output filenames include `training_time`.
   - But the command invoking `micro_ideal_UNIFORM_DIST` does not pass `--ideal-training-time={training_time}`.
   - As a result, the documented training-interval sweep for the lazy-delete experiment is not actually applied by the released script.

2. **--ideal-training-time falls through to abort() in bench.cpp**
   - In `parse_args`, `case 'z'` assigns `ideal_training_interval` but has no `break;`.
   - It therefore falls through to `default: abort();`.
   - So simply adding the missing argument to `lazy_delete.py` is not sufficient; the parser also needs a `break`.

3. **Twitter node-size sweep does not pass the node-size/error-bound settings**
   - `scripts/node_size.py` loops over `NODE_ACCURACY_THRESHOLD_LIST=(8, 16, 24, 32)`.
   - The YCSB command correctly passes `--sindex-group-err-bound` and `--sindex-root-err-bound`.
   - The Twitter command does not pass either setting, while still labeling result files by `node_accuracy`.

4. **--bg is parsed but ignored by the SIndex microbenchmark**
   - `bench.cpp` parses `--bg` into `bg_n`.
   - `prepare_sindex()` constructs the index with a hard-coded background-worker count of `1`.
   - Thus changing `--bg` does not affect the constructed SIndex instance.

5. **CMake blocks for SIndex-family benchmark targets are commented out**
   - The blocks defining `original`, `sia-sw`, and `ideal` performance/microbenchmark targets are currently commented.
   - This conflicts with the README/scripts that expect those binaries to exist after the documented CMake build.

6. **README microbenchmark executable name does not match the CMake target naming**
   - README shows `PERFORMANCE_sia-sw_bench_{DISTRIBUTION}`.
   - The CMake microbenchmark target naming is `micro_{Index}_{Dist}`.

### Validation

I put these checks into a small automated audit and ran it against a fresh clone:

- pristine artifact: **6/6 defects detected**
- after narrow guarded fixes: **0/6 detected**
- restored CMake target `micro_ideal_UNIFORM_DIST`: **build succeeded**
- smoke test with `--ideal-training-time=5`: **ran successfully after the parser/script fixes**

The fixes used for the smoke test were intentionally narrow:
- use `bg_n` instead of hard-coded `1`
- add `break` to `case 'z'`
- pass `--ideal-training-time={training_time}` in `lazy_delete.py`
- pass the SIndex error-bound options in the Twitter node-size sweep
- restore the commented SIndex benchmark target blocks
- correct the README microbenchmark target name

If useful, I can provide the focused patch/diff for these artifact fixes.
