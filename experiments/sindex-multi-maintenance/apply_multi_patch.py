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
            f"Patch guard failed for {rel}: expected exactly 1 match, found {count}. "
            "Upstream or measurement patch may have changed."
        )
    path.write_text(text.replace(old, new, 1))
    print(f"[patched] {rel}")

replace_once(
    "original/sindex_impl.h",
    '''#include "sindex_root_impl.h"

#if !defined(SINDEX_IMPL_H)
''',
    '''#include "sindex_root_impl.h"

#include <cstdlib>
#include <fcntl.h>
#include <sys/file.h>

#if !defined(SINDEX_IMPL_H)
''',
    marker="#include <sys/file.h>"
)

replace_once(
    "original/sindex_impl.h",
    '''    if (!index.bg_running) break;

    DEBUG_THIS("------ [bg] new round of structure update");
''',
    '''    if (!index.bg_running) break;

    // Optional process-wide coordination experiment. When SINDEX_BG_LOCK_PATH
    // is set, each complete adjustment round acquires an inter-process flock.
    // Foreground queries never take this lock.
    int global_bg_lock_fd = -1;
    const char *global_bg_lock_path = std::getenv("SINDEX_BG_LOCK_PATH");
    if (global_bg_lock_path != nullptr && global_bg_lock_path[0] != '\0') {
      global_bg_lock_fd = open(global_bg_lock_path, O_CREAT | O_RDWR, 0666);
      if (global_bg_lock_fd < 0) {
        perror("open SINDEX_BG_LOCK_PATH");
        abort();
      }
      if (flock(global_bg_lock_fd, LOCK_EX) != 0) {
        perror("flock LOCK_EX");
        abort();
      }
    }

    DEBUG_THIS("------ [bg] new round of structure update");
''',
    marker="Optional process-wide coordination experiment"
)

replace_once(
    "original/sindex_impl.h",
    '''    memory_fence();  // ensure the background theads and the workers all see a
    rcu_barrier();   // correct final stage of root.groups
  }
''',
    '''    memory_fence();  // ensure the background theads and the workers all see a
    rcu_barrier();   // correct final stage of root.groups

    if (global_bg_lock_fd >= 0) {
      flock(global_bg_lock_fd, LOCK_UN);
      close(global_bg_lock_fd);
      // Yield briefly so another index waiting on the global token can run.
      usleep(1000);
    }
  }
''',
    marker="Yield briefly so another index waiting"
)

replace_once(
    "bench.cpp",
    '''#include <algorithm>
#include <atomic>
#include <array>
#include <cmath>
#include <memory>
''',
    '''#include <algorithm>
#include <atomic>
#include <array>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <memory>
''',
    marker="#include <chrono>"
)

replace_once(
    "bench.cpp",
    '''  COUT_THIS("[micro] prepare data ...");
  while (ready_threads < fg_n) sleep(1);

  running = true;
''',
    '''  COUT_THIS("[micro] prepare data ...");
  while (ready_threads < fg_n) sleep(1);

  // Multi-instance experiments can give every process the same absolute
  // start time so their measured windows overlap instead of being shifted by
  // different initialization times.
  const char *start_epoch_env = std::getenv("SINDEX_START_EPOCH_MS");
  if (start_epoch_env != nullptr && start_epoch_env[0] != '\0') {
    const long long target_ms = atoll(start_epoch_env);
    while (true) {
      const auto now = std::chrono::system_clock::now().time_since_epoch();
      const long long now_ms =
          std::chrono::duration_cast<std::chrono::milliseconds>(now).count();
      if (now_ms >= target_ms) break;
      const long long remaining_ms = target_ms - now_ms;
      usleep((useconds_t)(std::min<long long>(remaining_ms, 10) * 1000));
    }
  }

  running = true;
''',
    marker="Multi-instance experiments can give every process"
)

print("Multi-index coordination patch completed successfully.")
