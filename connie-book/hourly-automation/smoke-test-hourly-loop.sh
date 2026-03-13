#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
AUTOMATION_DIR="$SCRIPT_DIR"
RUNNER="$AUTOMATION_DIR/run-hourly-loop.sh"
TMP_DIR=$(mktemp -d "${TMPDIR:-/tmp}/connie-hourly-smoke.XXXXXX")
FAKE_CODEX="$TMP_DIR/codex"

cleanup() {
  rm -rf "$TMP_DIR"
}

trap cleanup EXIT HUP INT TERM

cat >"$FAKE_CODEX" <<'EOF'
#!/bin/sh

set -eu

OUTPUT_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-last-message)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [ -n "$OUTPUT_FILE" ]; then
  printf 'Smoke test final message\n' >"$OUTPUT_FILE"
fi

printf '{"type":"agent_message","message":"smoke-test-run"}\n'
EOF

chmod +x "$FAKE_CODEX"

CODEX_BIN="$FAKE_CODEX" "$RUNNER"

LATEST_STATUS=$(ls -1t "$AUTOMATION_DIR"/runs/*.status.txt | head -n 1)
EVENT_FILE=$(awk -F= '/^events_file=/{print $2}' "$LATEST_STATUS")
FINAL_FILE=$(awk -F= '/^final_message_file=/{print $2}' "$LATEST_STATUS")
PROMPT_FILE=$(awk -F= '/^prompt_file=/{print $2}' "$LATEST_STATUS")

grep -q '^exit_status=0$' "$LATEST_STATUS"
grep -q 'smoke-test-run' "$EVENT_FILE"
grep -q 'Smoke test final message' "$FINAL_FILE"
test -s "$PROMPT_FILE"

printf 'latest_status=%s\n' "$LATEST_STATUS"
printf 'event_file=%s\n' "$EVENT_FILE"
printf 'final_message_file=%s\n' "$FINAL_FILE"
printf 'prompt_file=%s\n' "$PROMPT_FILE"
