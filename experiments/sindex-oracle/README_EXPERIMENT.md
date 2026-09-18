# SIndex Oracle Maintenance-Scheduling Experiment

## Question

Can changing only the *timing* of background learned-index maintenance materially
improve foreground tail latency under a saturated mixed workload?

This is an oracle experiment, not a smart scheduler. If an oracle that knows
when to defer maintenance cannot help, a resource-aware scheduler is unlikely
to be worth building.

## Code path inspected

Public repository: `casys-kaist/sia`, `main`.

`original/sindex_impl.h` implements `SIndex::background()`, which creates
background workers and repeatedly starts `root_t::do_adjustment` rounds.

The upstream SIA README also identifies simultaneous CPU inference and training
as a performance bottleneck.

## Important upstream benchmark finding

`bench.cpp` parses `--bg`, but `prepare_sindex()` currently constructs SIndex
with a hard-coded background count of `1`. The patcher changes that to `bg_n`,
so `--bg=0` becomes a real control.

## Experiment

All runs use 30 seconds, 4 foreground threads, 80% reads / 20% inserts.

1. `normal`: background maintenance always allowed.
2. `oracle_pause`: no **new** adjustment round may begin during seconds 10–20.
3. `no_bg`: maintenance disabled, as an upper-bound/control only.

The patch samples 1/1024 operation latencies and emits phase-specific p50, p95,
p99, and p99.9. Compare phase 1 between `normal` and `oracle_pause`.

## Predeclared exploratory gate

- p99 improvement >= 20%
- phase operation count loss <= 5%

Failing this means kill or redesign before building a scheduler.

## Important limitations

- Pause is between adjustment rounds, not mid-round preemption.
- Backlog/catch-up is not yet measured.
- Dedicated-core isolation is not yet compared.
- Repeated trials and confidence intervals come only after the smoke test.
