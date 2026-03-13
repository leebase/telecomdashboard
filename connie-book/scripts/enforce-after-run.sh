#!/usr/bin/env bash

set -euo pipefail

LIVE_REPO_ROOT="/Users/leeharrington/projects/telecom-metadata"
LIVE_CONNIE_BOOK_ROOT="${LIVE_REPO_ROOT}/connie-book"
RUN_LOG_PATH="${LIVE_CONNIE_BOOK_ROOT}/RUN_LOG.md"
BACKLOG_PATH="${LIVE_CONNIE_BOOK_ROOT}/BACKLOG.md"

sync_connie_book() {
  rsync -a --delete \
    --exclude 'symphony-reference/' \
    --exclude 'symphony-logs/' \
    --exclude 'hourly-automation/runs/' \
    --exclude 'hourly-automation/runtime.log' \
    ./connie-book/ "${LIVE_CONNIE_BOOK_ROOT}/"
}

query_linear() {
  local payload="$1"

  curl -s https://api.linear.app/graphql \
    -H "Authorization: ${LINEAR_API_KEY}" \
    -H "Content-Type: application/json" \
    --data-binary @- <<EOF
${payload}
EOF
}

build_graphql_payload() {
  local query="$1"
  local variables_json="$2"

  python3 -c '
import json
import sys

print(json.dumps({
    "query": sys.argv[1],
    "variables": json.loads(sys.argv[2]),
}))
' "$query" "$variables_json"
}

read_json_field() {
  local field_path="$1"

  python3 -c '
import json
import sys

payload = json.load(sys.stdin)
value = payload
for part in sys.argv[1].split("."):
    if part.isdigit():
        value = value[int(part)]
    else:
        value = value.get(part)
    if value is None:
        break
if isinstance(value, str):
    print(value)
' "$field_path"
}

extract_backlog_id() {
  local title="$1"

  printf '%s\n' "$title" | sed -n 's/.*\(CBOOK-[0-9][0-9][0-9]\).*/\1/p' | head -n 1
}

artifact_path_for_backlog_id() {
  local backlog_id="$1"

  sed -n "/^### ${backlog_id}\$/,/^### /p" "${BACKLOG_PATH}" \
    | sed '1d;$d' \
    | sed -n 's/^- `artifact_path`: `\([^`]*\)`/\1/p' \
    | head -n 1
}

backlog_state_for_id() {
  local backlog_id="$1"

  sed -n "/^### ${backlog_id}\$/,/^### /p" "${BACKLOG_PATH}" \
    | sed '1d;$d' \
    | sed -n 's/^- `state`: \(.*\)$/\1/p' \
    | head -n 1
}

normalize_backlog_state_if_needed() {
  local backlog_id="$1"

  BACKLOG_ID="${backlog_id}" perl -0pi -e '
    my $id = $ENV{BACKLOG_ID};
    s/(### \Q$id\E\n.*?- `state`: )Done(\n)/${1}Ready$2/s;
  ' "${BACKLOG_PATH}"
}

append_guard_log() {
  local issue_identifier="$1"
  local backlog_id="$2"
  local artifact_path="$3"

  local next_run_id
  next_run_id="$(awk '/^## Run / {run=$3} END {printf "%03d", run + 1}' "${RUN_LOG_PATH}")"

  cat >> "${RUN_LOG_PATH}" <<EOF

## Run ${next_run_id}

- \`run_id\`: ${next_run_id}
- \`timestamp\`: $(date '+%Y-%m-%d %H:%M %Z')
- \`selected_item\`: ${backlog_id}
- \`participating_agents\`: Program Director, Editor and QA Agent
- \`goal\`: Enforce the post-run artifact guard after Symphony moved ${issue_identifier} to \`Done\` without leaving the required live artifact.
- \`artifacts_changed\`: \`RUN_LOG.md\`
- \`proof_of_work\`: The repo-owned \`after_run\` guard detected that \`${artifact_path}\` was still missing from the live source tree after a Symphony completion attempt, so it reopened ${issue_identifier} to \`Todo\` and preserved the backlog item as non-terminal work.
- \`blockers\`: The required artifact still does not exist in the live source tree.
- \`workflow_improvement\`: Completion enforcement now runs in executable hook logic instead of relying only on prompt compliance.
- \`next_recommended_item\`: ${backlog_id}
EOF
}

main() {
  sync_connie_book

  if [ -z "${LINEAR_API_KEY:-}" ]; then
    echo "after_run guard: LINEAR_API_KEY is not set; skipping tracker enforcement" >&2
    exit 0
  fi

  local issue_identifier
  issue_identifier="$(basename "$PWD")"

  case "${issue_identifier}" in
    *-*) ;;
    *)
      echo "after_run guard: workspace ${issue_identifier} is not a tracker issue workspace; sync only" >&2
      exit 0
      ;;
  esac

  local team_key issue_number
  team_key="${issue_identifier%%-*}"
  issue_number="${issue_identifier#*-}"

  if ! printf '%s' "${issue_number}" | grep -Eq '^[0-9]+$'; then
    echo "after_run guard: workspace ${issue_identifier} does not end with a numeric issue number; sync only" >&2
    exit 0
  fi

  local issue_payload issue_id issue_title issue_state backlog_id artifact_path artifact_abs backlog_state
  issue_payload="$(query_linear "$(build_graphql_payload \
    'query ConnieBookIssueByIdentifier($teamKey:String!,$number:Float!){ issues(filter:{ team:{ key:{ eq:$teamKey } }, number:{ eq:$number } }, first:1) { nodes { id identifier title state { name } } } }' \
    "$(printf '{"teamKey":"%s","number":%s}' "${team_key}" "${issue_number}")"
  )")"

  issue_id="$(printf '%s' "${issue_payload}" | read_json_field 'data.issues.nodes.0.id')"
  issue_title="$(printf '%s' "${issue_payload}" | read_json_field 'data.issues.nodes.0.title')"
  issue_state="$(printf '%s' "${issue_payload}" | read_json_field 'data.issues.nodes.0.state.name')"

  if [ -z "${issue_id}" ] || [ -z "${issue_title}" ] || [ -z "${issue_state}" ]; then
    echo "after_run guard: could not resolve Linear issue metadata for ${issue_identifier}; sync only" >&2
    exit 0
  fi

  backlog_id="$(extract_backlog_id "${issue_title}")"

  if [ -z "${backlog_id}" ]; then
    echo "after_run guard: Linear title ${issue_title} does not carry a Connie backlog id; sync only" >&2
    exit 0
  fi

  artifact_path="$(artifact_path_for_backlog_id "${backlog_id}")"

  if [ -z "${artifact_path}" ]; then
    echo "after_run guard: ${backlog_id} has no artifact gate; sync only" >&2
    exit 0
  fi

  artifact_abs="${LIVE_REPO_ROOT}/${artifact_path}"

  if [ "${issue_state}" != "Done" ]; then
    echo "after_run guard: ${issue_identifier} is ${issue_state}; no terminal-state enforcement needed" >&2
    exit 0
  fi

  if [ -f "${artifact_abs}" ]; then
    echo "after_run guard: ${artifact_path} exists; allowing Done state for ${issue_identifier}" >&2
    exit 0
  fi

  local todo_state_payload todo_state_id
  todo_state_payload="$(query_linear "$(build_graphql_payload \
    'query ConnieBookResolveTodo($issueId:String!,$stateName:String!){ issue(id:$issueId) { team { states(filter:{ name:{ eq:$stateName } }, first:1) { nodes { id } } } } }' \
    "$(printf '{"issueId":"%s","stateName":"Todo"}' "${issue_id}")"
  )")"
  todo_state_id="$(printf '%s' "${todo_state_payload}" | read_json_field 'data.issue.team.states.nodes.0.id')"

  if [ -z "${todo_state_id}" ]; then
    echo "after_run guard: could not resolve Todo state id for ${issue_identifier}; sync only" >&2
    exit 0
  fi

  query_linear "$(build_graphql_payload \
    'mutation ConnieBookReopenIssue($issueId:String!,$stateId:String!){ issueUpdate(id:$issueId, input:{ stateId:$stateId }) { success } }' \
    "$(printf '{"issueId":"%s","stateId":"%s"}' "${issue_id}" "${todo_state_id}")"
  )" >/dev/null

  query_linear "$(build_graphql_payload \
    'mutation ConnieBookComment($issueId:String!,$body:String!){ commentCreate(input:{ issueId:$issueId, body:$body }) { success } }' \
    "$(python3 -c 'import json, sys; print(json.dumps({"issueId": sys.argv[1], "body": sys.argv[2]}))' "${issue_id}" "Auto-guard reopened ${issue_identifier}: required artifact ${artifact_abs} was still missing after the Symphony run. Leave this issue non-terminal until the file exists in the live source tree and the Connie backlog stays aligned.")"
  )" >/dev/null

  backlog_state="$(backlog_state_for_id "${backlog_id}")"
  if [ "${backlog_state}" = "Done" ]; then
    normalize_backlog_state_if_needed "${backlog_id}"
  fi

  append_guard_log "${issue_identifier}" "${backlog_id}" "${artifact_path}"
  echo "after_run guard: reopened ${issue_identifier} because ${artifact_path} is missing" >&2
}

main "$@"
