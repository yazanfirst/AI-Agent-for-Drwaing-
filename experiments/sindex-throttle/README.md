# SIndex Maintenance Throttling Experiment

This follows the failed ON/OFF oracle experiment.

Instead of pausing maintenance, this experiment preserves the original
maintenance algorithm and controls its coarse duty cycle:

- 100% (baseline)
- 75%
- 50%
- 25%

After each complete adjustment round, the system rests for a time derived from
that round's active duration. For example, at 50% duty, a round that takes T is
followed by about T of idle time.

Predeclared exploratory gate for any throttled setting:
- p99 improvement >= 10% vs 100%
- p99.9 worsening <= 10%
- phase operation-count loss <= 5%

This is a screening experiment, not publication-grade evidence.
