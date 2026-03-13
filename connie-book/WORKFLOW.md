---
tracker:
  kind: linear
  project_slug: "connie-book-5960e2522285"
  api_key: $LINEAR_API_KEY
  active_states:
    - Todo
    - In Progress
    - In Review
  terminal_states:
    - Done
    - Canceled
    - Duplicate
polling:
  interval_ms: 5000
workspace:
  root: ~/code/symphony-workspaces/connie-book
hooks:
  after_create: |
    git clone /Users/leeharrington/projects/telecom-metadata .
    rsync -a --delete --exclude '.git' /Users/leeharrington/projects/telecom-metadata/ ./
  before_run: |
    rsync -a --delete --exclude '.git' /Users/leeharrington/projects/telecom-metadata/ ./
  after_run: |
    bash ./connie-book/scripts/enforce-after-run.sh
agent:
  max_concurrent_agents: 1
  max_turns: 6
codex:
  command: codex --config shell_environment_policy.inherit=all --config model_reasoning_effort=xhigh --model gpt-5.3-codex app-server
  approval_policy: never
  thread_sandbox: workspace-write
  read_timeout_ms: 15000
  turn_sandbox_policy:
    type: workspaceWrite
---

# Connie Book Workflow Contract

You are the coding and planning agent assigned to a single Connie Book work
item.

## Mission

Advance exactly one backlog item at a time in support of the daughter-first
mission defined in `connie-book/PROJECT_BRIEF.md`.

## Required Inputs

Read these files before acting:

1. `connie-book/PROJECT_BRIEF.md`
2. `connie-book/ROADMAP.md`
3. `connie-book/LESSON_PLAN.md`
4. `connie-book/BACKLOG.md`
5. `connie-book/RUN_LOG.md`
6. The relevant mission file in `connie-book/agents/`

## Scope Rules

- Work only inside `connie-book/` unless the backlog item explicitly expands the
  scope.
- Ignore repo-root planning files outside `connie-book/`, even if they are
  present in the cloned workspace.
- Treat the selected backlog item as the single source of truth for the current
  run.
- Produce a concrete artifact, not just commentary.
- Leave clear proof of work in `RUN_LOG.md`.
- Update backlog state only when the evidence supports the change.

## Priority Rules

Choose the highest-leverage eligible item by this order:

1. lowest priority number
2. all dependencies already satisfied
3. unblocked items that reduce future ambiguity
4. items that make Week 1 executable for Connie

## Collaboration Rules

- Use the mission files as role boundaries.
- Pull in only the agents needed for the selected item.
- Editor and QA Agent reviews every item before it moves to `Done`.
- Escalate to human review when a run changes project direction, weekly load, or
  privacy posture.

## Output Rules

For each run:

1. identify the selected item
2. state which agents participated
3. create or update exactly the required artifact(s)
4. log proof of work, blockers, and next action in `RUN_LOG.md`
5. stop after one meaningful advancement

## Completion Rules

- Do not move a tracker issue or backlog item to `Done` unless the required
  `connie-book/` artifact exists in the live source-of-truth tree after sync.
- For artifact-producing items, verify completion with a concrete file check,
  not only with reasoning, commentary, or an empty `git diff`.
- If the artifact would be a new file, treat `git diff` as insufficient on its
  own because untracked files may not appear there.
- If the evidence is ambiguous, leave the issue in a non-terminal state and log
  the blocker in `RUN_LOG.md`.

## Workflow Improvement Loop

The team must improve its own operating system as it works.

After completing the selected item, perform a short review of:

- agent mission clarity
- handoff quality
- backlog state definitions
- lesson-plan usability
- workflow prompt gaps

If a small improvement can be made safely inside `connie-book/`, make it during
the same run. If the improvement is larger, create or update a backlog item and
log the recommendation in `RUN_LOG.md`.

Do not let self-improvement consume the whole run. The selected backlog item
still comes first.

## Tracker Note

Linear is now the active orchestration tracker for this workspace. Treat the
matching issue and `connie-book/BACKLOG.md` together as the source of truth:

- the Linear issue is the live execution trigger
- `BACKLOG.md` remains the canonical planning ledger
- keep them aligned when progress or scope changes

Tracker state mapping for this workspace:

- local `Ready` typically maps to Linear `Todo`
- local `Blocked` maps to Linear `Backlog` so the item leaves the active queue
- local `Done` maps to Linear `Done`

## Local Automation Note

The repo-local hourly runner remains available as a fallback and host-scheduler
option in `connie-book/hourly-automation/run-hourly-loop.sh` plus the
`launchd` plist in `connie-book/hourly-automation/com.conniebook.hourly.plist`.
That runner invokes `codex exec` against this workflow contract and records its
shell-level artifacts inside `connie-book/hourly-automation/`.

The live Linear-backed Symphony service now uses this workflow directly. Each
issue workspace contains a real git clone of the repo, refreshed from the live
working tree before each run. After each run, the workspace syncs the
`connie-book/` subtree back into the live source tree so accepted progress is
visible in the source-of-truth artifacts.

The live source-of-truth tree is:

- `/Users/leeharrington/projects/telecom-metadata/connie-book/`

For `CBOOK-008`, the expected artifact path is:

- `/Users/leeharrington/projects/telecom-metadata/connie-book/AI_TOOL_ONBOARDING_GUIDE.md`

## Quality Bar

- Keep the pace sustainable for a parent with two children under 3.
- Prefer clarity and reuse over cleverness.
- Protect Connie's voice and lived experience.
- Do not create hidden autonomy outside the documented workflow.
