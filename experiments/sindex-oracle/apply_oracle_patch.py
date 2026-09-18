#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

def replace_once(rel, old, new, marker=None):
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"Missing expected file: {path}")
    text = path.read_text()
    if marker and marker in text:
        print(f"[already patched] {rel}: {marker}")
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"Patch guard failed for {rel}: expected exactly 1 match, found {count}.\n"
            "The upstream source may have changed; inspect before applying."
        )
    path.write_text(text.replace(old, new, 1))
    print(f"[patched] {rel}")

replace_once(
    "original/sindex.h",
    '''  size_t range_scan(const key_t &begin, const key_t &end,
                    std::vector<std::pair<key_t, val_t>> &result,
                    const uint32_t worker_id);
 private:
''',
    '''  size_t range_scan(const key_t &begin, const key_t &end,
                    std::vector<std::pair<key_t, val_t>> &result,
                    const uint32_t worker_id);

  // Oracle experiment control. Pausing prevents a NEW adjustment round
  // from starting; an already-running round is allowed to finish safely.
  inline void set_bg_paused(bool paused) {
    bg_paused.store(paused, std::memory_order_release);
  }
  inline bool is_bg_paused() const {
    return bg_paused.load(std::memory_order_acquire);
  }

 private:
''',
    marker="Oracle experiment control"
)

replace_once(
    "original/sindex.h",
    '''  size_t bg_num;
  volatile bool bg_running = true;
};
''',
    '''  size_t bg_num;
  volatile bool bg_running = true;
  std::atomic<bool> bg_paused{false};
};
''',
    marker="bg_paused{false}"
)

replace_once(
    "original/sindex_impl.h",
    '''  while (index.bg_running) {
    DEBUG_THIS("------ [bg] new round of structure update");
''',
    '''  while (index.bg_running) {
    // Oracle experiment: defer the next maintenance round while foreground
    // service is in the protected window. Do not interrupt a round already
    // in progress because that could violate the adjustment protocol.
    while (index.bg_running &&
           index.bg_paused.load(std::memory_order_acquire)) {
      usleep(1000);
    }
    if (!index.bg_running) break;

    DEBUG_THIS("------ [bg] new round of structure update");
''',
    marker="Oracle experiment: defer the next maintenance round"
)

replace_once(
    "bench.cpp",
    '''#include <algorithm>
#include <atomic>
#include <memory>
''',
    '''#include <algorithm>
#include <atomic>
#include <array>
#include <cmath>
#include <memory>
''',
    marker="#include <array>"
)

replace_once(
    "bench.cpp",
    '''size_t fg_n = 1;
size_t bg_n = 1;
size_t seed = SEED;

volatile bool running = false;
std::atomic<size_t> ready_threads(0);
''',
    '''size_t fg_n = 1;
size_t bg_n = 1;
size_t seed = SEED;
double oracle_pause_start = -1.0;
double oracle_pause_end = -1.0;

volatile bool running = false;
std::atomic<size_t> ready_threads(0);
std::atomic<int> benchmark_phase(0);  // 0=pre, 1=oracle-window, 2=post
''',
    marker="oracle_pause_start"
)

replace_once(
    "bench.cpp",
    '''struct alignas(CACHELINE_SIZE) FGParam {
  sindex_t *table;
  uint64_t throughput;
  uint32_t thread_id;

  double latency_sum;
  int latency_count;
''',
    '''struct alignas(CACHELINE_SIZE) FGParam {
  sindex_t *table;
  uint64_t throughput;
  std::array<uint64_t, 3> phase_throughput;
  uint32_t thread_id;

  double latency_sum;
  int latency_count;
  std::array<std::vector<uint64_t>, 3> latency_samples_ns;
''',
    marker="phase_throughput"
)

replace_once(
    "bench.cpp",
    '''  std::vector<uint64_t> vals(exist_keys.size(), 1);
  table = new sindex_t(exist_keys, vals, fg_n, 1);
}
''',
    '''  std::vector<uint64_t> vals(exist_keys.size(), 1);
  // Upstream parses --bg, but this microbenchmark hard-coded 1 here.
  // Use bg_n so --bg=0 is a real no-maintenance control.
  table = new sindex_t(exist_keys, vals, fg_n, bg_n);
}
''',
    marker="real no-maintenance control"
)

replace_once(
    "bench.cpp",
    '''    struct timespec begin_t, end_t;

    while (running) {
''',
    '''    struct timespec begin_t, end_t;
    uint64_t local_op_count = 0;

    while (running) {
''',
    marker="local_op_count"
)

replace_once(
    "bench.cpp",
    '''        clock_gettime(CLOCK_MONOTONIC, &end_t);
        thread_param.latency_sum += (end_t.tv_sec - begin_t.tv_sec) + (end_t.tv_nsec - begin_t.tv_nsec) / 1000000000.0;
        thread_param.latency_count++;
        thread_param.throughput++;
    }
''',
    '''        clock_gettime(CLOCK_MONOTONIC, &end_t);
        const uint64_t latency_ns =
            (uint64_t)(end_t.tv_sec - begin_t.tv_sec) * 1000000000ULL +
            (uint64_t)(end_t.tv_nsec - begin_t.tv_nsec);
        thread_param.latency_sum += latency_ns / 1000000000.0;
        thread_param.latency_count++;
        thread_param.throughput++;

        const int phase = benchmark_phase.load(std::memory_order_relaxed);
        thread_param.phase_throughput[phase]++;

        // Sample one in every 1024 operations to limit observer overhead.
        local_op_count++;
        if ((local_op_count & 1023ULL) == 0) {
          thread_param.latency_samples_ns[phase].push_back(latency_ns);
        }
    }
''',
    marker="Sample one in every 1024"
)

replace_once(
    "bench.cpp",
    '''    fg_params[worker_i].thread_id = worker_i;
    fg_params[worker_i].throughput = 0;
    fg_params[worker_i].latency_count = 0;
''',
    '''    fg_params[worker_i].thread_id = worker_i;
    fg_params[worker_i].throughput = 0;
    fg_params[worker_i].phase_throughput = {0, 0, 0};
    fg_params[worker_i].latency_count = 0;
''',
    marker="phase_throughput = {0, 0, 0}"
)

replace_once(
    "bench.cpp",
    '''  uint64_t total_keys = initial_size;
  double current_sec = 0.0;

  while (current_sec < sec) {
''',
    '''  uint64_t total_keys = initial_size;
  double current_sec = 0.0;
  const bool oracle_enabled =
      oracle_pause_start >= 0.0 &&
      oracle_pause_end > oracle_pause_start &&
      oracle_pause_end <= (double)sec;

  while (current_sec < sec) {
    if (oracle_enabled) {
      if (current_sec >= oracle_pause_start &&
          current_sec < oracle_pause_end) {
        benchmark_phase.store(1, std::memory_order_relaxed);
        table->set_bg_paused(true);
      } else if (current_sec >= oracle_pause_end) {
        benchmark_phase.store(2, std::memory_order_relaxed);
        table->set_bg_paused(false);
      } else {
        benchmark_phase.store(0, std::memory_order_relaxed);
        table->set_bg_paused(false);
      }
    } else {
      // Label the middle third as phase 1 in the normal/control runs so
      // it can be compared against the oracle's paused window.
      const double p1 = sec / 3.0;
      const double p2 = 2.0 * sec / 3.0;
      benchmark_phase.store(current_sec < p1 ? 0 :
                            (current_sec < p2 ? 1 : 2),
                            std::memory_order_relaxed);
    }
''',
    marker="const bool oracle_enabled"
)

replace_once(
    "bench.cpp",
    '''  running = false;
  void *status;

  double all_latency_sum = 0.0;
  int all_latency_count = 0;
  for (size_t i = 0; i < fg_n; i++) {
    all_latency_count += fg_params[i].latency_count;
''',
    '''  running = false;
  table->set_bg_paused(false);
  void *status;

  double all_latency_sum = 0.0;
  int all_latency_count = 0;
  for (size_t i = 0; i < fg_n; i++) {
    int rc = pthread_join(threads[i], &status);
    if (rc) {
      COUT_N_EXIT("Error:unable to join," << rc);
    }

    all_latency_count += fg_params[i].latency_count;
''',
    marker="int rc = pthread_join(threads[i], &status);"
)

path = ROOT / "bench.cpp"
text = path.read_text()
stale = '''    //int rc = pthread_join(threads[i], &status);
    //if (rc) {
    //  COUT_N_EXIT("Error:unable to join," << rc);
    //}
'''
if stale in text:
    path.write_text(text.replace(stale, "", 1))
    print("[patched] bench.cpp: removed stale commented join block")

replace_once(
    "bench.cpp",
    '''  std::cout << final_buf.str();
  std::flush(std::cout);
  #endif
''',
    '''  std::cout << final_buf.str();
  std::flush(std::cout);

  auto percentile = [](std::vector<uint64_t> &v, double q) -> uint64_t {
    if (v.empty()) return 0;
    std::sort(v.begin(), v.end());
    size_t idx = (size_t)std::ceil(q * v.size()) - 1;
    if (idx >= v.size()) idx = v.size() - 1;
    return v[idx];
  };

  for (int phase = 0; phase < 3; ++phase) {
    std::vector<uint64_t> samples;
    uint64_t phase_ops = 0;
    for (size_t i = 0; i < fg_n; ++i) {
      phase_ops += fg_params[i].phase_throughput[phase];
      samples.insert(samples.end(),
                     fg_params[i].latency_samples_ns[phase].begin(),
                     fg_params[i].latency_samples_ns[phase].end());
    }
    std::cout
      << "ORACLE_RESULT"
      << ",phase=" << phase
      << ",ops=" << phase_ops
      << ",samples=" << samples.size()
      << ",p50_ns=" << percentile(samples, 0.50)
      << ",p95_ns=" << percentile(samples, 0.95)
      << ",p99_ns=" << percentile(samples, 0.99)
      << ",p999_ns=" << percentile(samples, 0.999)
      << std::endl;
  }
  #endif
''',
    marker="ORACLE_RESULT"
)

replace_once(
    "bench.cpp",
    '''      {"ideal-training-time", required_argument, 0, 'z'},
      {0, 0, 0, 0}};
''',
    '''      {"ideal-training-time", required_argument, 0, 'z'},
      {"oracle-pause-start", required_argument, 0, 1001},
      {"oracle-pause-end", required_argument, 0, 1002},
      {0, 0, 0, 0}};
''',
    marker='"oracle-pause-start"'
)

replace_once(
    "bench.cpp",
    '''      case 'z':
        ideal_training_interval = strtoul(optarg, NULL, 10);
      default:
        abort();
''',
    '''      case 'z':
        ideal_training_interval = strtoul(optarg, NULL, 10);
        break;
      case 1001:
        oracle_pause_start = strtod(optarg, NULL);
        break;
      case 1002:
        oracle_pause_end = strtod(optarg, NULL);
        break;
      default:
        abort();
''',
    marker="case 1001:"
)

replace_once(
    "bench.cpp",
    '''  COUT_VAR(runtime);
  COUT_VAR(fg_n);
  COUT_VAR(bg_n);
''',
    '''  COUT_VAR(runtime);
  COUT_VAR(fg_n);
  COUT_VAR(bg_n);
  COUT_VAR(oracle_pause_start);
  COUT_VAR(oracle_pause_end);
''',
    marker="COUT_VAR(oracle_pause_start)"
)

print("\nPatch completed successfully.")
