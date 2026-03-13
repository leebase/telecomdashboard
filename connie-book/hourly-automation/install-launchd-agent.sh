#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
SOURCE_PLIST="$SCRIPT_DIR/com.conniebook.hourly.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/com.conniebook.hourly.plist"
LABEL="com.conniebook.hourly"
DOMAIN="gui/$(id -u)"

mkdir -p "$(dirname "$TARGET_PLIST")"
cp "$SOURCE_PLIST" "$TARGET_PLIST"

launchctl bootout "$DOMAIN" "$TARGET_PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "$DOMAIN" "$TARGET_PLIST"
launchctl kickstart -k "$DOMAIN/$LABEL"
launchctl print "$DOMAIN/$LABEL"
