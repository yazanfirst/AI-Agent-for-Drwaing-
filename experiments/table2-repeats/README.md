# Repeated Table 2 screen

The released `scripts/lazy_delete.py` sets `REPEAT_NUM=1`. Earlier corrected
runs on the same GitHub runner showed materially different 5s-vs-300s
degradation values, so a single run is not enough to interpret the gap from
the paper.

This experiment repeats each 10M-key / 16-foreground-thread condition three
times. It uses paired comparisons and reverses 5s/300s execution order in the
second repetition to reduce simple order bias.

Outputs include the three degradation values, mean, sample standard deviation,
and an exploratory 95% t-interval (df=2). The CI is intentionally labeled
screening-only because n=3 is small.
