#!/bin/sh
set -e

system-anchor-create rotation
system-replicate

# destroy anchor on source only
snap=$(zfs list -t snap -s creation -Ho name $TEST_ROOT \
        | grep rotation- | tail -n1)
zfs release repl-anchor $snap
zfs destroy "$snap"

system-snapshot t1

capture_status system-replicate

assert_command_fail expected missing anchor failure
echo "$OUTPUT" | assert_grep "base snapshot missing"
