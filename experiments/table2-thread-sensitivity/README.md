# Table 2 thread-sensitivity experiment

The paper's evaluation machine has 16 CPU cores. GitHub's hosted runner exposes
4 CPUs. The near-paper-scale experiment intentionally kept the artifact's
16 foreground threads, which oversubscribes the runner 4x.

This experiment holds 10M initial keys and the delete mixes fixed, and compares
the 5s-vs-300s degradation with:
- 4 foreground threads (matches available CPUs)
- 16 foreground threads (matches the released artifact / paper-era script)

If the reported degradation changes substantially, the Table 2 effect is
hardware/thread-scheduling sensitive and exact reproduction needs hardware
closer to the paper's 16-core Xeon system.
