<pre>
xls: 103
title: Migrating xrpld to Structured Logging
description: A phased migration of the xrpld core logging infrastructure from unstructured Beast log to high-performance, structured JSON logging via spdlog.
author: Developer
status: Draft
category: System
created: 2026-04-23
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

## 3. Detailed Design
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

## 4. Migration Challenges & Solutions

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

## 5. Implementation Plan
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

## 6. Request for Comments (Community Feedback)
We deeply value the community's input on this transition. Your operational insights are critical to ensuring `xrpld` continues to meet your monitoring and reliability standards. While the architectural decision to move towards structured JSON logging is a necessary modernization step to keep pace with industry standards, we are eager to hear your thoughts on the mechanics of the rollout, default configurations, and formatting details. We encourage all node operators to share their feedback, detail the observability tooling they rely on, and let us know how this phased approach fits into their workflows so we can take it under thorough advisement during implementation.