# Connie Book Hourly Orchestration Runbook

## Purpose

This runbook defines the local hourly automation loop that advances Connie Book
work before a full tracker-backed Symphony deployment is available.

## Live Automation Artifacts

- Runner: `connie-book/hourly-automation/run-hourly-loop.sh`
- Scheduler: `connie-book/hourly-automation/com.conniebook.hourly.plist`
- Host installer: `connie-book/hourly-automation/install-launchd-agent.sh`
- Host verifier: `connie-book/hourly-automation/verify-launchd-agent.sh`
- Local smoke test: `connie-book/hourly-automation/smoke-test-hourly-loop.sh`
- Runtime evidence: `connie-book/hourly-automation/runtime.log`
- Per-run artifacts: `connie-book/hourly-automation/runs/`

The current implementation is intentionally repo-local. It invokes `codex exec`
against `connie-book/WORKFLOW.md`, keeps all logs inside `connie-book/`, and
stops after one backlog item per wake-up.

## Hourly Loop

1. Read `PROJECT_BRIEF.md`, `ROADMAP.md`, `LESSON_PLAN.md`, `BACKLOG.md`,
   `RUN_LOG.md`, and `WORKFLOW.md`.
2. Select the highest-priority eligible backlog item whose dependencies are
   satisfied.
3. Load only the mission files needed for that item.
4. Advance one artifact meaningfully.
5. Update `BACKLOG.md` only if the evidence supports a state change.
6. Append a new entry to `RUN_LOG.md`.
7. Perform a brief workflow-and-agent improvement review.
8. Stop after one item.

## Installation

Use `launchd` on macOS to run the loop every hour from a host terminal:

1. `connie-book/hourly-automation/install-launchd-agent.sh`
2. `launchctl print gui/$(id -u)/com.conniebook.hourly`

The plist uses `RunAtLoad` plus `StartInterval = 3600`, so the first run starts
as soon as the agent is bootstrapped and then repeats hourly.

This install step is expected to be run by the workspace owner on the host
machine. During Symphony-issued runs, direct `launchctl bootstrap` calls from
the nested agent environment returned `Input/output error`, and the same
failure reproduced with a minimal throwaway plist in `/tmp`. Activation
therefore cannot be verified from inside the agent environment alone.

## Uninstall

Remove the scheduled loop with:

- `connie-book/hourly-automation/uninstall-launchd-agent.sh`

## Verification

Preflight the runner without networked Codex access:

- `connie-book/hourly-automation/smoke-test-hourly-loop.sh`

Verify the installed `launchd` job and print the newest recorded run:

- `connie-book/hourly-automation/verify-launchd-agent.sh`

If host installation fails, run these checks from the host terminal:

- `plutil -lint "$HOME/Library/LaunchAgents/com.conniebook.hourly.plist"`
- `launchctl print gui/$(id -u)/com.conniebook.hourly`
- `sed -n '1,80p' connie-book/hourly-automation/launchd.stderr.log`
- `sed -n '1,80p' connie-book/hourly-automation/launchd.stdout.log`

Check these files after installation or after a manual `launchctl kickstart`:

- `connie-book/hourly-automation/runtime.log`
- `connie-book/hourly-automation/launchd.stdout.log`
- `connie-book/hourly-automation/launchd.stderr.log`
- the newest file set in `connie-book/hourly-automation/runs/`

Each run should produce:

- a generated prompt snapshot
- a JSONL event stream from `codex exec`
- a stderr log
- the final agent message
- a status file with timestamps and exit code

## Item Selection Rules

- Prefer lower priority numbers first.
- Prefer items that reduce ambiguity for Week 1 execution.
- Prefer items that unblock other ready work.
- If two items are tied, prefer the one that yields a reusable artifact.

## Tracker Alignment

- If a local item becomes `Blocked`, move the Linear issue to `Backlog`, not
  `Todo`.
- `Todo` is part of the active orchestration queue in `WORKFLOW.md`.
- Use `Backlog` to keep blocked work visible without re-triggering the hourly
  loop.

## Allowed Changes

- Planning documents inside `connie-book/`
- Agent mission files inside `connie-book/agents/`
- Backlog state and definitions
- Lesson-plan refinements
- Run-log entries
- Repo-local automation artifacts for the hourly loop

## Disallowed Changes

- Editing the rest of the repo unless a backlog item expands scope explicitly
- Publishing content externally
- Inventing new high-workload commitments without human review

## Workflow Improvement Review

At the end of every run, answer these questions:

1. Did the selected agent mission leave ambiguity?
2. Did the handoff require guessing?
3. Did the backlog item need a better definition of done?
4. Did the lesson-plan pacing feel unrealistic?
5. Should a new backlog item be added to improve the system itself?

If the answer to any question is yes:

- make the smallest safe improvement now, or
- add a backlog item and record it in `RUN_LOG.md`

## Stop Conditions

Stop the run immediately if:

- the next change would alter project direction
- the next change would increase weekly workload materially
- the next change would affect privacy posture
- the backlog item is blocked by a human decision
