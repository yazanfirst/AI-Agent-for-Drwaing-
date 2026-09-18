#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

def replace_once(rel, old, new, marker=None):
    path = ROOT / rel
    text = path.read_text()
    if marker and marker in text:
        print(f"[already patched] {rel}: {marker}")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Patch guard failed for {rel}: expected 1 match, found {count}. "
            "Upstream may have changed."
        )
    path.write_text(text.replace(old, new, 1))
    print(f"[patched] {rel}")

replace_once(
    "original/sindex_util.h",
    """  size_t group_min_size = 400;
  std::unique_ptr<rcu_status_t[]> rcu_status;
""",
    """  size_t group_min_size = 400;
  // Fraction of wall time background maintenance should be active.
  // 1.0 = unthrottled. 0.5 ~= work for T, then rest for T.
  double bg_duty_cycle = 1.0;
  std::unique_ptr<rcu_status_t[]> rcu_status;
""",
    marker="double bg_duty_cycle = 1.0;"
)

replace_once(
    "original/sindex_impl.h",
    """#include "sindex_root_impl.h"

#if !defined(SINDEX_IMPL_H)
""",
    """#include "sindex_root_impl.h"
#include <chrono>

#if !defined(SINDEX_IMPL_H)
""",
    marker="#include <chrono>"
)

replace_once(
    "original/sindex_impl.h",
    """    DEBUG_THIS("------ [bg] new round of structure update");

    for (size_t bg_i = 0; bg_i < bg_num; bg_i++) {
""",
    """    const auto throttle_round_begin = std::chrono::steady_clock::now();
    DEBUG_THIS("------ [bg] new round of structure update");

    for (size_t bg_i = 0; bg_i < bg_num; bg_i++) {
""",
    marker="throttle_round_begin"
)

replace_once(
    "original/sindex_impl.h",
    """    memory_fence();  // ensure the background theads and the workers all see a
    rcu_barrier();   // correct final stage of root.groups
  }
""",
    """    memory_fence();  // ensure the background theads and the workers all see a
    rcu_barrier();   // correct final stage of root.groups

    // Coarse maintenance throttling: preserve the existing maintenance logic,
    // but insert an idle interval after each complete adjustment round.
    // If a round takes T and duty=d, sleep T*(1/d - 1).
    const double duty = config.bg_duty_cycle;
    if (index.bg_running && duty > 0.0 && duty < 0.999999) {
      const auto throttle_round_end = std::chrono::steady_clock::now();
      const auto active_us =
          std::chrono::duration_cast<std::chrono::microseconds>(
              throttle_round_end - throttle_round_begin).count();
      const long long idle_us =
          (long long)(active_us * ((1.0 / duty) - 1.0));
      if (idle_us > 0) usleep((useconds_t)idle_us);
    }
  }
""",
    marker="Coarse maintenance throttling"
)

replace_once(
    "bench.cpp",
    """      {"oracle-pause-end", required_argument, 0, 1002},
      {0, 0, 0, 0}};
""",
    """      {"oracle-pause-end", required_argument, 0, 1002},
      {"bg-duty", required_argument, 0, 1003},
      {0, 0, 0, 0}};
""",
    marker='{"bg-duty"'
)

replace_once(
    "bench.cpp",
    """      case 1002:
        oracle_pause_end = strtod(optarg, NULL);
        break;
      default:
""",
    """      case 1002:
        oracle_pause_end = strtod(optarg, NULL);
        break;
      case 1003:
        sindex::config.bg_duty_cycle = strtod(optarg, NULL);
        INVARIANT(sindex::config.bg_duty_cycle > 0.0 &&
                  sindex::config.bg_duty_cycle <= 1.0);
        break;
      default:
""",
    marker="case 1003:"
)

replace_once(
    "bench.cpp",
    """  COUT_VAR(oracle_pause_end);
  COUT_VAR(sindex::config.root_error_bound);
""",
    """  COUT_VAR(oracle_pause_end);
  COUT_VAR(sindex::config.bg_duty_cycle);
  COUT_VAR(sindex::config.root_error_bound);
""",
    marker="COUT_VAR(sindex::config.bg_duty_cycle)"
)

print("Throttle patch completed successfully.")
