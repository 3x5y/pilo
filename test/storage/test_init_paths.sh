#!/bin/sh
set -e

capture_status pilo storage-init

assert_command_ok "init should succeed with valid layout"

[ -d "$PILO_PATH/admin" ] || fail "default admin path missing"
[ -d "$PILO_PATH/pile" ] || fail "default pile path missing"
