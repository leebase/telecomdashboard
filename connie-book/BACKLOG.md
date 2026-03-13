# Connie Book Backlog

This backlog uses issue-like records so the work can be run manually now and
ported into a Symphony tracker flow later.

## State Definitions

- `Done`: completed and reflected in the current artifacts
- `Ready`: eligible to be picked up now
- `Blocked`: waiting on another item, a host-side action, or a human decision
- `Proposed`: useful, but not yet part of the current near-term queue

## Tracker Mapping Note

Linear does not currently have a dedicated `Blocked` state for this workspace.
When a local backlog item moves to `Blocked`, mirror the matching Linear issue
to `Backlog`, not `Todo`. `Todo` is an active orchestration state in
`WORKFLOW.md`, while `Backlog` keeps blocked work out of the hourly wake-up
queue until the blocker is removed.

## Backlog Summary

| ID | Title | Priority | State | Owner Agent | Dependencies | Milestone |
|----|-------|----------|-------|-------------|--------------|-----------|
| CBOOK-000 | Bootstrap the workspace and planning docs | 1 | Done | Program Director | none | M1 Bootstrap |
| CBOOK-001 | Define the cooperative agent team | 1 | Done | Program Director | CBOOK-000 | M1 Bootstrap |
| CBOOK-002 | Draft the 90-day roadmap | 1 | Done | Curriculum Architect | CBOOK-000 | M1 Bootstrap |
| CBOOK-003 | Draft the 12-week lesson plan | 1 | Done | Curriculum Architect | CBOOK-002 | M1 Bootstrap |
| CBOOK-004 | Create the Symphony-compatible workflow contract | 1 | Done | Program Director | CBOOK-000 | M1 Bootstrap |
| CBOOK-005 | Simulate the first orchestration run | 1 | Done | Editor and QA Agent | CBOOK-001, CBOOK-002, CBOOK-003, CBOOK-004 | M1 Bootstrap |
| CBOOK-006 | Decide the book category and reader promise | 1 | Ready | Writing Coach | none | M2 Book Framing |
| CBOOK-007 | Build the Week 1 packet and first-session checklist | 2 | Ready | Curriculum Architect | CBOOK-003, CBOOK-006 | M2 Book Framing |
| CBOOK-008 | Create the AI tool onboarding guide | 2 | Ready | AI Tools Coach | CBOOK-003 | M2 Book Framing |
| CBOOK-009 | Research 10 comparable books and reference models | 2 | Ready | Research and Reference Agent | CBOOK-006 | M2 Book Framing |
| CBOOK-010 | Define the portfolio evidence checklist | 2 | Ready | Editor and QA Agent | CBOOK-003, CBOOK-008 | M4 Portfolio Proof |
| CBOOK-011 | Activate a real hourly automation loop | 1 | Blocked | Program Director | CBOOK-004, CBOOK-005 | M1 Bootstrap |
| CBOOK-012 | Improve agent missions and workflow feedback loop | 2 | Done | Editor and QA Agent | CBOOK-001, CBOOK-004, CBOOK-005 | M1 Bootstrap |
| CBOOK-013 | Connect a real tracker-backed Symphony service | 3 | Ready | Program Director | CBOOK-004 | M1 Bootstrap |
| CBOOK-014 | Replace Linear with a project-owned tracker adapter | 3 | Proposed | Program Director | CBOOK-013 | M1 Bootstrap |

## Detailed Items

### CBOOK-000

- `id`: CBOOK-000
- `title`: Bootstrap the workspace and planning docs
- `description`: Create the source-of-truth files in `connie-book/` so the
  project has a usable operating system before further work begins.
- `priority`: 1
- `state`: Done
- `owner_agent`: Program Director
- `dependencies`: none
- `definition_of_done`: `PROJECT_BRIEF.md`, `ROADMAP.md`, `LESSON_PLAN.md`,
  `BACKLOG.md`, `WORKFLOW.md`, `agents/`, and `RUN_LOG.md` all exist.

### CBOOK-001

- `id`: CBOOK-001
- `title`: Define the cooperative agent team
- `description`: Establish agent responsibilities, boundaries, and handoff
  rules so future runs do not invent roles on the fly.
- `priority`: 1
- `state`: Done
- `owner_agent`: Program Director
- `dependencies`: CBOOK-000
- `definition_of_done`: Each agent mission file exists with objective, inputs,
  outputs, boundaries, collaboration rules, handoff criteria, and done
  criteria.

### CBOOK-002

- `id`: CBOOK-002
- `title`: Draft the 90-day roadmap
- `description`: Define the first quarter's milestones, weekly cadence, and
  expected outputs.
- `priority`: 1
- `state`: Done
- `owner_agent`: Curriculum Architect
- `dependencies`: CBOOK-000
- `definition_of_done`: `ROADMAP.md` contains phased milestones, weekly rhythm,
  and quarter exit criteria.

### CBOOK-003

- `id`: CBOOK-003
- `title`: Draft the 12-week lesson plan
- `description`: Write a practical curriculum that ties book-writing work to AI
  tool learning every week.
- `priority`: 1
- `state`: Done
- `owner_agent`: Curriculum Architect
- `dependencies`: CBOOK-002
- `definition_of_done`: `LESSON_PLAN.md` contains all 12 weeks with writing
  goal, AI goal, deliverable, exercise, time budget, and artifact.

### CBOOK-004

- `id`: CBOOK-004
- `title`: Create the Symphony-compatible workflow contract
- `description`: Define the repo-owned workflow policy and execution prompt that
  a future Symphony runner can use.
- `priority`: 1
- `state`: Done
- `owner_agent`: Program Director
- `dependencies`: CBOOK-000
- `definition_of_done`: `WORKFLOW.md` contains YAML front matter plus an
  execution prompt that constrains work to `connie-book/`.

### CBOOK-005

- `id`: CBOOK-005
- `title`: Simulate the first orchestration run
- `description`: Demonstrate one end-to-end run from backlog selection through
  proof of work so the operating model is explicit.
- `priority`: 1
- `state`: Done
- `owner_agent`: Editor and QA Agent
- `dependencies`: CBOOK-001, CBOOK-002, CBOOK-003, CBOOK-004
- `definition_of_done`: `RUN_LOG.md` contains a concrete example with selected
  item, participants, outputs, blockers, and next action.

### CBOOK-006

- `id`: CBOOK-006
- `title`: Decide the book category and reader promise
- `description`: Narrow the possible book directions to one working category and
  one draft promise to the reader.
- `priority`: 1
- `state`: Ready
- `owner_agent`: Writing Coach
- `dependencies`: none
- `definition_of_done`: A short memo exists naming the working category, ideal
  reader, and the main payoff the book should offer.

### CBOOK-007

- `id`: CBOOK-007
- `title`: Build the Week 1 packet and first-session checklist
- `description`: Turn Week 1 of the lesson plan into a concrete starter packet
  Connie can use immediately.
- `priority`: 2
- `state`: Ready
- `owner_agent`: Curriculum Architect
- `dependencies`: CBOOK-003, CBOOK-006
- `definition_of_done`: A simple packet exists with a session checklist, story
  inventory prompt, and voice-note exercise.

### CBOOK-008

- `id`: CBOOK-008
- `title`: Create the AI tool onboarding guide
- `description`: Define the minimum starter toolset and a low-stress learning
  sequence for using AI during writing work.
- `priority`: 2
- `state`: Ready
- `owner_agent`: AI Tools Coach
- `dependencies`: CBOOK-003
- `definition_of_done`: `AI_TOOL_ONBOARDING_GUIDE.md` exists in
  `connie-book/` and explains the starter tools, what each tool is for, and
  when not to use it.
- `artifact_path`: `connie-book/AI_TOOL_ONBOARDING_GUIDE.md`

### CBOOK-009

- `id`: CBOOK-009
- `title`: Research 10 comparable books and reference models
- `description`: Gather strong examples that can help with positioning, tone,
  structure, and reader expectations.
- `priority`: 2
- `state`: Ready
- `owner_agent`: Research and Reference Agent
- `dependencies`: CBOOK-006
- `definition_of_done`: A comparison sheet exists with at least 10 books or
  reference models and short notes on why each matters.

### CBOOK-010

- `id`: CBOOK-010
- `title`: Define the portfolio evidence checklist
- `description`: Decide which artifacts will best prove AI-enabled writing and
  practical operating skill over the quarter.
- `priority`: 2
- `state`: Ready
- `owner_agent`: Editor and QA Agent
- `dependencies`: CBOOK-003, CBOOK-008
- `definition_of_done`: A checklist exists naming the artifacts to retain, the
  evidence standard for each, and the review owner.

### CBOOK-011

- `id`: CBOOK-011
- `title`: Activate a real hourly automation loop
- `description`: Move from a documented hourly process to a real scheduled run
  once the local workflow is trusted.
- `priority`: 1
- `state`: Blocked
- `owner_agent`: Program Director
- `dependencies`: CBOOK-004, CBOOK-005
- `definition_of_done`: An automation exists that wakes hourly, reviews the
  backlog, advances one item, and records the run output.
- `blocking_note`: The repo-local runner, scheduler plist, and host install
  scripts exist, plus a passing local smoke test and host verification helpers,
  but `launchctl bootstrap` returned `Input/output error` from the nested agent
  environment for both the Connie Book plist and a minimal `/tmp` smoke plist.
  A host-terminal install and first live run verification are still required.

### CBOOK-012

- `id`: CBOOK-012
- `title`: Improve agent missions and workflow feedback loop
- `description`: Add a recurring mechanism for the team to refine its own
  prompts, handoffs, and backlog rules as it learns what is working.
- `priority`: 2
- `state`: Done
- `owner_agent`: Editor and QA Agent
- `dependencies`: CBOOK-001, CBOOK-004, CBOOK-005
- `definition_of_done`: The workflow contract, run log, and backlog explicitly
  support agent and workflow improvement without derailing normal item
  execution.

### CBOOK-013

- `id`: CBOOK-013
- `title`: Connect a real tracker-backed Symphony service
- `description`: Replace the repo-local backlog-only operating mode with a live
  tracker-backed Symphony runtime when the project is ready.
- `priority`: 3
- `state`: Ready
- `owner_agent`: Program Director
- `dependencies`: CBOOK-004
- `definition_of_done`: A real tracker source, workflow file, and Symphony
  runtime are connected and able to run against the project safely.
- `implementation_note`: Linear is connected, the upstream Symphony daemon is
  running, and the repo-owned `after_run` guard now reopens false terminal
  transitions when required artifacts are missing. The remaining gap is one
  clean end-to-end artifact-producing run that leaves the expected file in the
  live `connie-book/` tree without needing the guard to intervene.

### CBOOK-014

- `id`: CBOOK-014
- `title`: Replace Linear with a project-owned tracker adapter
- `description`: Reduce lock-in to Linear by designing a project-owned issue
  source or adapter that can keep the Connie Book workflow aligned with
  upstream Symphony while removing the long-term dependency on Linear as the
  sole tracker.
- `priority`: 3
- `state`: Proposed
- `owner_agent`: Program Director
- `dependencies`: CBOOK-013
- `definition_of_done`: The project has a documented replacement strategy for
  Linear, including the minimal tracker interface needed by Symphony, the
  migration path from Linear, and a plan for preserving compatibility with
  upstream improvements.
