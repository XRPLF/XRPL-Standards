<pre>
  xls: 103
  title: Migrating xrpld to Structured Logging
  description: A phased migration of the xrpld core logging infrastructure from unstructured Beast log to high-performance, structured JSON logging via spdlog.
  author: Jingchen Wu (@a1q123456)
  category: System
  status: Draft
  proposal-from: https://github.com/XRPLF/XRPL-Standards/discussions/524
  created: 2026-04-23
  updated: 2026-04-23
</pre>

# Migrating xrpld to Structured Logging

## 1. Abstract

This standard proposes a phased migration of the `xrpld` core logging infrastructure from the legacy, unstructured Beast log system to a high-performance, structured JSON logging system utilizing `spdlog`. By introducing structured logging, we aim to drastically improve node observability, debugging efficiency, and interoperability with modern telemetry pipelines (e.g., OpenTelemetry, ELK stack, Datadog), while simultaneously enhancing logging performance under heavy node load.

## 2. Motivation

Currently, `xrpld` relies on Beast log for emitting text-based log messages. While human-readable, unstructured text poses significant challenges for automated parsing, monitoring, and at-scale debugging. Migrating to structured (JSON) logging via `spdlog` offers significant advantages:

### 2.1. Performance Improvements
* **Async Logging:** The current system holds a mutex and writes to `std::cerr` + `std::ofstream` synchronously, which blocks the calling thread under heavy load (e.g., during consensus or connection storms). `spdlog`'s async mode utilizes a lock-free queue and a background thread, allowing the caller to return immediately.
* **Zero Heap Allocations via fmt:** `spdlog` utilizes `fmt`-style formatting. This is significantly faster and more readable than building a `std::stringstream` and chaining `operator<<`, completely avoiding heap allocations.
* **No Per-Call StringStreams:** Currently, every triggered `JLOG` constructs a `ScopedStream` containing a `std::ostringstream`, resulting in a heap allocation per log message. `spdlog` formats directly into a pre-allocated thread-local buffer.
* **Compile-Time Level Elimination:** `spdlog` allows setting `SPDLOG_ACTIVE_LEVEL`, completely compiling out log calls below a threshold for zero runtime cost. 

### 2.2. Feature Enhancements
* **Enhanced Debugging & OpenTelemetry:** Emitting structured JSON logs allows operators to feed logs directly into observability pipelines without parsing free-text lines. You can directly query exact fields (e.g., transaction hashes, peer IPs, or error codes).
* **Built-in Log Rotation:** The current `Logs::File` requires a manual, RPC-triggered `closeAndReopen()`. `spdlog` provides `rotating_file_sink` and `daily_file_sink` out of the box with configurable size and time policies.
* **Native Multiple Sinks:** `spdlog` seamlessly supports writing to multiple destinations simultaneously (e.g., file, stderr, syslog) using `spdlog::sinks::dist_sink`.

## 3. Specification

### 3.1. Core Components

The core architecture for integrating structured logging will rely on the following components and design choices:

1. **`JsonLoggingPatternBuilder`**: A utility class responsible for taking a set of parameters and baking them into the JSON log pattern. It supports taking an existing log pattern and appending new parameters to it seamlessly.
2. **Logger Injection**: Components within `xrpld` will transition to passing `spdlog` loggers directly, entirely replacing the current practice of passing `beast::Journal`.
3. **Optimized Pattern Storage**: Log patterns will be stored directly within the loggers themselves, ensuring there is no additional overhead or unnecessary string copying during runtime execution.
4. **Hybrid Formatting**: Text will be formatted and injected alongside the structured parameters within the resulting JSON object. This ensures operators retain a human-readable message field while systems can index the raw keys.

**Example Usage in C++:**
```cpp
rpcLogger->info("node: {key1}, some additional information: {key2}", 
    log::params("key1", "value1"),
    log::params("key2", true),
    log::params("key3", 99)
);
```

**Resulting JSON Output:**
```json
{
  "timestamp": "2026-04-23T09:00:00Z",
  "logger": "1",
  "log_level": "info",
  "channel": "RPC",
  "process_id": 123,
  "thread_id": 123,
  "message": "node: value1, some additional information: true",
  "params": {
    "key1": "value1",
    "key2": true,
    "key3": 99
  }
}
```

### 3.2. Migration Challenges & Solutions

Given the pervasive nature of logging in the codebase, we anticipate several migration challenges:

| Issue | Detail | Solution |
|-------|--------|----------|
| **Journal passed by value everywhere** | `beast::Journal` is a tiny value type copied into hundreds of classes. | Hold a raw pointer to the `spdlog` logger, equally cheap to copy. |
| **Sink abstraction used for formatting** | `WrappedSink` prepends prefixes, `Logs::Sink` adds partition names. | Use `spdlog` custom formatters for partition/prefix injection; use `spdlog` sinks for output destinations. |
| **Test sink injection** | `SuiteJournalSink` and `CaptureSink` intercept logs for test assertions. | Write equivalent `spdlog::sinks::sink` subclasses; keep `makeSink()` factory on the `Logs` replacement. |
| **Per-partition runtime severity control** | `Logs` maintains per-partition thresholds, adjustable at runtime via RPC. | Use `spdlog` named loggers — each partition gets its own independently settable level. |
| **Log rotation via RPC** | `Logs::rotate()` triggered by RPC command. | Use `spdlog`'s `rotating_file_sink` for automatic rotation, or implement RPC-triggered rotation by swapping the file sink. |
| **JLOG lazy evaluation** | `JLOG` short-circuits `operator<<` chains when level is inactive. | Use `SPDLOG_LOGGER_CALL` macros or equivalent for runtime/compile-time elimination. |
| **`debugLog()` global sink** | `DebugSink` is a swappable global singleton. | Replace with a named `spdlog` logger (e.g., `spdlog::get("debug")`). |

### 3.3. Implementation Plan

The migration will be rolled out in distinct phases across multiple Pull Requests (PRs) to minimize disruption.

* **Phase 0: Integrate spdlog (PR 1)**
  * Introduce `spdlog` as a core dependency.
  * *No implementation* of JSON logging will occur here. The Beast log infrastructure remains untouched.
* **Phase 1: Implement JSON Logging & Testing (PR 2)**
  * Implement `JsonLoggingPatternBuilder` and structured wrappers.
  * Introduce comprehensive unit tests.
  * Add a configuration option to enable JSON logging, **defaulted to OFF**.
* **Phase 2: Deprecate Beast Log**
  * Systematically replace all legacy Beast log calls throughout the codebase.
  * Fully remove the Beast log infrastructure.
* **Phase 3: Review exisitng logs**
  * With OpenTelemetry, we're able to tell which logs are unnecessary and should be removed.

## 4. Rationale

The architectural decision to move towards structured JSON logging is a necessary modernization step to keep pace with industry standards. The phased rollout approach was chosen to minimize disruption to the existing infrastructure: introducing `spdlog` as a dependency first (with no behavior change), then layering structured logging on top behind a feature flag, before finally deprecating the Beast log system. This reduces the blast radius of any single PR and allows the community to validate each phase independently.

Community input is deeply valued in this transition. Node operators' operational insights are critical to ensuring `xrpld` continues to meet monitoring and reliability standards. Feedback on the mechanics of the rollout, default configurations, and formatting details — as well as details of the observability tooling operators rely on — will be taken under thorough advisement during implementation.

## 5. Security Considerations

The migration from Beast log to `spdlog` does not alter the logical behavior of `xrpld` or the XRP Ledger protocol. However, the following security aspects are relevant:

* **Log injection:** Structured JSON logging reduces the risk of log injection attacks compared to free-text logging, as fields are serialized with strict type boundaries rather than concatenated strings.
* **Information disclosure:** Operators should review which fields are included in structured log output (especially when enabling JSON logging in production) to ensure no sensitive data (e.g., private keys, internal state) is inadvertently emitted. The existing `scrubber` function in `Logs.cpp`, which redacts sensitive keying material before log messages are emitted, will be carried forward and applied to structured log fields in the new implementation.
* **Async queue overflow:** The async logging mode introduces a bounded lock-free queue. Under extreme load, the queue may overflow and drop log messages. This is a reliability concern (not a security vulnerability), but operators should configure queue sizes appropriately.
* **Dependency supply chain:** Introducing `spdlog` as a new core dependency adds a new surface for supply-chain risk. The dependency should be pinned to a reviewed version and monitored for upstream security advisories.