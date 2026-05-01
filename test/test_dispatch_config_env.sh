#!/bin/sh
set -eu

CONF="$TMP/pilo.conf"

cat > "$CONF" <<EOF
PILO_ROOT=$TEST_ROOT
PILO_PATH=/$TEST_ROOT
EOF

unset PILO_ROOT
unset PILO_PATH

export PILO_CONFIG="$CONF"

capture_status pilo status pile

assert_command_ok
