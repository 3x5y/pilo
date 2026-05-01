#!/bin/sh
set -e

# layout created in test setup
capture_status pilo init

assert_command_ok "init should succeed with valid layout"
