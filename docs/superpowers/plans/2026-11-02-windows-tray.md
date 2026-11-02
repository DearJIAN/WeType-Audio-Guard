# Windows Tray Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

**Goal:** Deliver a default-paused Windows tray prototype on feat/windows-tray, with simulated safety tests and no changes to the validated CLI.

**Architecture:** Reuse GuardPolicy / WindowsAudio unchanged. A single audio worker runs in a dedicated spawned child process; its main thread owns COM. One parent supervisor thread exchanges commands and value-only snapshots. Process containment bounds shutdown when native COM hangs.

**Tech Stack:** Python 3.12, unittest, multiprocessing, pystray, Pillow, logging.

**Spec:** ../specs/2026-11-02-windows-tray-design.md, approved by user; latest user requirements take priority.

## Global Constraints

- Original CLI bytes and behavior unchanged; Windows only; no actual audio writes in automated verification.
- Default paused; discard baseline after enable/pause/errors; never learn baseline during recording.
- No EXE, startup settings, services, telemetry, auto-update, main merge or force push.

## Review Focus

- A native COM read/write can hang: bounded child cleanup, no UI wait on native calls.
- Pause racing a snapshot: revision filtering, explicit pending acknowledgement, no stale enable.
- Interrupted snapshots / device changes: no restoration using incomplete or stale baseline.
- Existing CLI protection: fail closed on detection or inability to inspect Python processes; document limitation of unchanged CLI.
- Logging and GUI callbacks: no COM references or sensitive error payloads cross process boundary.

## Tasks

- [x] 1. Add failing tests for guard engine safety and lifecycle, implement tray_runtime.py with injectable audio, COM hooks, and clock. Preserve per-recording attempt ledger even after transient errors.
- [x] 2. Add failing tests for real Windows mutex isolation, CLI conflict detection, logging, worker pause/shutdown. Implement tray_platform.py and process controller in tray_runtime.py.
- [x] 3. Add failing icon/menu tests; implement tray_icon.py and wetype_audio_tray.py, add requirements-tray.txt, install declared dependencies.
- [x] 4. Generate and inspect 16/24/32 icon previews, update README and acceptance guide, run CLI baseline checks and full unittest discovery.
- [x] 5. Fresh branch review; fix meaningful findings with regression tests; commit, push feat/windows-tray and verify remote source tree, main and visibility.

## Decisions / ledger

Ruling: Contain the audio main worker thread in a spawned child process rather than an unkillable in-process thread. UI retains one supervisor thread. Normal toggles reuse the child; a hung child is stopped and requires explicit re-enable. This is the smallest reliable way to bound exit without modifying the CLI. Cost: an extra Python process while tray runs.

Ruling: Pausing is asynchronous and explicitly shown as pending until the audio worker acknowledges; native calls already entered cannot be revoked. Timeout terminates only the owned child, and state becomes paused/error. Cost: up to the watchdog timeout before pause confirmation for a stuck call.

Ruling: Unchanged CLI cannot honor a new mutex. Detect CLI --protect at start, enable and before each write and refuse tray protection on detection/inspection failure. Document remaining race if CLI starts exactly between inspection and write. Cost: detection is conservative and cannot provide a two-sided lock without changing CLI.


## Execution results

Tasks 1–4 complete. Original CLI remains byte-identical; 36 tests pass including spawned-process safety, real Windows mutex, simulated COM ownership and native paused tray smoke. Native audio protection was not run.

Final review: two Important snapshot findings verified and fixed with failing regression tests followed by a green 36-test suite. No Critical findings or deferred minors. Additional availability regression fixed for opaque non-Python processes.

Final: Ruling: Only identified Python processes with unreadable command lines block advisory CLI exclusion; opaque process names cannot be reliably classified without elevation. Document this alongside renamed interpreters and script copies. Cost if wrong: an unidentifiable CLI could be missed, so users must never run both protection modes.

Final: Ruling: Real audio compatibility, device insertion/removal and display scaling remain user acceptance work, as explicitly required. Cost: these outcomes cannot be claimed validated before the user tests them.

Branch implementation and review complete; remote push and byte verification are checked before the final delivery report.
