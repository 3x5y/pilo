#!/bin/sh
set -e

capture_status pilo anchor-create daily

assert_command_ok failed to create daily anchor

zfs list -t snap | assert_grep "@daily-"
