#!/bin/sh
set -e

capture_status system-anchor-create daily

assert_command_ok failed to create daily anchor

zfs list -t snap | assert_grep "@daily-"
