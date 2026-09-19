# Near-paper-scale Table 2 screen

This is a stronger follow-up to the 500k-key screening test.

It matches the released lazy_delete.py on:
- 10,000,000 initial keys
- 16 foreground threads
- 30 second runtime
- 5%, 10%, 15% delete ratios

It compares only 5s and 300s training intervals, because that is the key
contrast reported in Table 2 and keeps cloud cost/time low.

Important limitation: GitHub-hosted runner hardware is not the Xeon Gold 6226R
machine used in the paper. hardware.txt records the actual runner resources.
Therefore numerical disagreement is evidence of artifact/environment
sensitivity, not by itself proof that the paper's original measurements were
wrong.
