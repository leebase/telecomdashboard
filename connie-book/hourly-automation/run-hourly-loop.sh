#!/bin/sh

set -eu
umask 077

PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
BOOK_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
WORKSPACE_ROOT=$(CDPATH= cd -- "$BOOK_DIR/.." && pwd)
AUTOMATION_DIR="$BOOK_DIR/hourly-automation"
RUN_DIR="$AUTOMATION_DIR/runs"
LOCK_DIR="$AUTOMATION_DIR/.lock"
RUNTIME_LOG="$AUTOMATION_DIR/runtime.log"
WORKFLOW_SOURCE="$BOOK_DIR/WORKFLOW.md"

CODEX_BIN=${CODEX_BIN:-}
if [ -z "$CODEX_BIN" ]; then
  CODEX_BIN=$(command -v codex || true)
fi

if [ -z "$CODEX_BIN" ]; then
  printf 'codex CLI not found in PATH\n' >&2
  exit 1
fi

mkdir -p "$RUN_DIR"

extract_workflow_prompt() {
  awk '
    NR == 1 && $0 == "---" {
      in_frontmatter = 1
      next
    }
    in_frontmatter && $0 == "---" {
      in_frontmatter = 0
      next
    }
    !in_frontmatter {
      print
    }
  ' "$WORKFLOW_SOURCE"
}

if [ "${1:-}" = "--dry-run" ]; then
  printf 'workspace_root=%s\n' "$WORKSPACE_ROOT"
  printf 'book_dir=%s\n' "$BOOK_DIR"
  printf 'codex_bin=%s\n' "$CODEX_BIN"
  printf 'workflow_source=%s\n' "$WORKFLOW_SOURCE"
  exit 0
fi

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  printf '%s overlapping run skipped\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')" >>"$RUNTIME_LOG"
  exit 0
fi

cleanup() {
  rmdir "$LOCK_DIR"
}

trap cleanup EXIT HUP INT TERM

RUN_STAMP=$(date '+%Y%m%d-%H%M%S')
PROMPT_FILE="$RUN_DIR/$RUN_STAMP.prompt.md"
EVENT_LOG="$RUN_DIR/$RUN_STAMP.events.jsonl"
STDERR_LOG="$RUN_DIR/$RUN_STAMP.stderr.log"
FINAL_MESSAGE="$RUN_DIR/$RUN_STAMP.final.txt"
STATUS_FILE="$RUN_DIR/$RUN_STAMP.status.txt"
STARTED_AT=$(date '+%Y-%m-%d %H:%M:%S %Z')

{
  printf '# Scheduled Run Context\n\n'
  printf -- '- `invocation_time`: %s\n' "$STARTED_AT"
  printf -- '- `workspace_root`: `%s`\n' "$WORKSPACE_ROOT"
  printf -- '- `automation_source`: `connie-book/hourly-automation/run-hourly-loop.sh`\n'
  printf -- '- `selection_mode`: repo-local backlog rules described in `connie-book/WORKFLOW.md` and `connie-book/HOURLY_ORCHESTRATION.md`\n'
  printf -- '- `guardrail`: advance at most one backlog item and record proof in `connie-book/RUN_LOG.md`\n\n'
  extract_workflow_prompt
} >"$PROMPT_FILE"

printf '%s run started: %s\n' "$STARTED_AT" "$RUN_STAMP" >>"$RUNTIME_LOG"

STATUS=0
"$CODEX_BIN" -a never exec \
  --skip-git-repo-check \
  --cd "$WORKSPACE_ROOT" \
  --sandbox workspace-write \
  --model gpt-5.3-codex \
  --config shell_environment_policy.inherit=all \
  --config model_reasoning_effort=xhigh \
  --color never \
  --json \
  --output-last-message "$FINAL_MESSAGE" \
  - <"$PROMPT_FILE" >"$EVENT_LOG" 2>"$STDERR_LOG" || STATUS=$?

FINISHED_AT=$(date '+%Y-%m-%d %H:%M:%S %Z')

{
  printf 'run_stamp=%s\n' "$RUN_STAMP"
  printf 'started_at=%s\n' "$STARTED_AT"
  printf 'finished_at=%s\n' "$FINISHED_AT"
  printf 'exit_status=%s\n' "$STATUS"
  printf 'prompt_file=%s\n' "$PROMPT_FILE"
  printf 'events_file=%s\n' "$EVENT_LOG"
  printf 'stderr_file=%s\n' "$STDERR_LOG"
  printf 'final_message_file=%s\n' "$FINAL_MESSAGE"
} >"$STATUS_FILE"

printf '%s run finished: %s status=%s\n' "$FINISHED_AT" "$RUN_STAMP" "$STATUS" >>"$RUNTIME_LOG"

exit "$STATUS"
