#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
AUTOMATION_DIR="$SCRIPT_DIR"
TARGET_PLIST="$HOME/Library/LaunchAgents/com.conniebook.hourly.plist"
LABEL="com.conniebook.hourly"
DOMAIN="gui/$(id -u)"

if [ ! -f "$TARGET_PLIST" ]; then
  printf 'missing_plist=%s\n' "$TARGET_PLIST" >&2
  exit 1
fi

printf 'installed_plist=%s\n' "$TARGET_PLIST"
launchctl print "$DOMAIN/$LABEL"

LATEST_STATUS=$(ls -1t "$AUTOMATION_DIR"/runs/*.status.txt 2>/dev/null | head -n 1 || true)

if [ -n "$LATEST_STATUS" ]; then
  printf 'latest_status=%s\n' "$LATEST_STATUS"
  awk -F= '
    /^started_at=/ { printf "started_at=%s\n", $2 }
    /^finished_at=/ { printf "finished_at=%s\n", $2 }
    /^exit_status=/ { printf "exit_status=%s\n", $2 }
    /^events_file=/ { printf "events_file=%s\n", $2 }
    /^final_message_file=/ { printf "final_message_file=%s\n", $2 }
  ' "$LATEST_STATUS"
else
  printf 'latest_status=missing\n'
fi
