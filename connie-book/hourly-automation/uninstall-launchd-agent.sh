#!/bin/sh

set -eu

TARGET_PLIST="$HOME/Library/LaunchAgents/com.conniebook.hourly.plist"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN" "$TARGET_PLIST" >/dev/null 2>&1 || true
rm -f "$TARGET_PLIST"
