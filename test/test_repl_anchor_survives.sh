#!/bin/sh
set -e

system-anchor-create rotation

snap=$(zfs list -t snap -s creation -Ho name | tail -n1)

capture_status zfs destroy "$snap"

assert_command_fail rotation anchor should be protected
