#!/bin/sh
set -e

capture_status pilo storage-snapshot-reg

assert_command_ok failed to create snapshot

snap=$(zfs list -t snap -s creation -Ho name | tail -n1)

zfs list "$snap" > /dev/null