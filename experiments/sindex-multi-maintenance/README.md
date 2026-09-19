# Cross-Index Maintenance Coordination Experiment

## Hypothesis

Modern learned-index designs make maintenance decisions locally inside one
index. In a DBMS with multiple learned indexes, independent background
adjustment rounds can overlap and contend for shared CPU/cache resources.

This experiment does **not** claim that global maintenance scheduling is a new
general database idea. Traditional DBMSs and LSM engines already coordinate
background maintenance. The question is narrower: does learned-index
maintenance exhibit enough cross-index interference to justify a
learned-index-specific global scheduler?

## Cheapest oracle

Run 2 and 4 independent SIndex instances concurrently.

- **local**: every index runs its own background adjustment normally.
- **serial**: adjustment rounds across all index processes share one global
  file-lock token, so only one index may perform a maintenance round at once.
  Foreground queries never acquire the token.

Each condition is repeated twice, with order reversed in repetition 2.

Metric for the screening test:
- aggregate foreground operations across all index instances;
- worst per-index p99 and p99.9;
- median per-index p99.

Predeclared GO gate:
- mean worst-index p99 improves by at least 10%;
- aggregate ops loss is no worse than 5%;
- p99 improves in both repetitions.

## Known limitation

The instances intentionally use the same default data/workload seed in this
first experiment. That tests a worst-case synchronized "maintenance storm".
If the signal survives, the next test must use heterogeneous seeds/workloads.
