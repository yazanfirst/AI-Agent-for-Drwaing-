# Small Table 2 reproduction

Goal: test whether the fixed public SIA artifact actually responds to the
cold-training interval in the direction reported for Table 2 before spending
resources on a full-scale reproduction.

Paper setup retained:
- ideal index
- 30 second benchmark runtime
- read/delete mixes: 95/5, 90/10, 85/15
- cold-training intervals: 5, 30, 100, 300 seconds

Scaled down for GitHub Actions:
- 4 foreground threads instead of the paper artifact script's 16
- 500,000 initial keys instead of 10,000,000
- 500,000 target/table size instead of 100,000,000

Therefore this is **not** a reproduction of the paper's numerical values.
It is only a screening experiment for whether the interval parameter changes
performance in the reported direction.

The paper reports the 300s interval degrades performance relative to the short
interval by about 3.2%, 4.1%, and 4.6% at 5%, 10%, and 15% delete ratios.
