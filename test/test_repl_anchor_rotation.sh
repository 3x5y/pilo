#!/bin/sh
set -e

capture_status system-anchor-create rotation

assert_command_ok failed to create rotation anchor

snap=$(zfs list -t snap -s creation -Ho name | tail -n1)

zfs holds "$snap" | assert_grep repl-anchor
