# Connie Book Symphony Setup Notes

## Current Operating Mode

The active orchestrator for this workspace is now the upstream Symphony Elixir
service, pointed at the real Connie Book Linear project and this repo-owned
`WORKFLOW.md`.

The repo still keeps two planning layers on purpose:

1. `connie-book/BACKLOG.md` remains the canonical planning ledger.
2. Linear issues are the live execution trigger that Symphony polls.

This preserves the upstream Symphony model while keeping the project's
structure and state definitions in-repo.

## Live Path For This Repo

The practical live setup for this repository is:

- keep the repo-local artifacts in `connie-book/` as the source of truth
- let Linear trigger work selection for the upstream Symphony daemon
- keep the repo-local hourly automation as a fallback and host-scheduler option
- constrain all agent edits to `connie-book/` through `WORKFLOW.md`

Current tracker target:

- Linear project URL: `https://linear.app/connie-book/project/connie-book-5960e2522285`
- Workflow `project_slug`: `connie-book-5960e2522285`
- Codex runtime: `codex-cli 0.113.0` with the upstream-style app-server
  command, explicit model selection, and extended read timeout
- Workspace bootstrap: each issue workspace gets a real repo clone, then the
  current live working tree is overlaid into it before every run
- Writeback path: the repo-owned `after_run` guard script
  `connie-book/scripts/enforce-after-run.sh` syncs the workspace
  `connie-book/` subtree back into
  `/Users/leeharrington/projects/telecom-metadata/connie-book/`
- Completion guard: that same script resolves the active Linear issue from the
  workspace identifier, checks any `artifact_path` recorded in `BACKLOG.md`,
  and reopens the issue to `Todo` if Symphony moved it to `Done` without the
  required live artifact
- Git repair note: the moved `telecom-metadata` worktree was reattached with
  `git worktree repair /Users/leeharrington/projects/telecom-metadata` from the
  parent `telecomdashboard` repo

## Remaining Stabilization Work

The remaining gap is no longer installation or tracker wiring. It is run
stability:

1. confirm one clean end-to-end Symphony run that edits the live
   `connie-book/` artifacts
2. verify the matching Linear issue state stays aligned with the evidence
3. keep the fallback hourly runner available until the live service is trusted

Recent runtime lesson:

- a tracker issue can still be closed incorrectly if the workflow does not
  require a concrete live-tree artifact check
- prompt-only completion rules were not sufficient, so completion enforcement
  now lives in the repo-owned `after_run` hook instead of in prompt text alone
- `CBOOK-008` is now pinned to the explicit artifact path
  `/Users/leeharrington/projects/telecom-metadata/connie-book/AI_TOOL_ONBOARDING_GUIDE.md`
  so the next retry has a sharper success condition
- the guard has been validated with a controlled `CON-6` replay: forcing the
  issue back to `Done` now reopens it automatically and leaves a Linear comment
  when the artifact is still missing

## Why This Is The Right Intermediate Step

- It creates real hourly progress immediately.
- It preserves the Symphony operating model.
- It avoids blocking on Linear configuration before the project is stable.
- It keeps the automation contained to `connie-book/` while the team learns.
