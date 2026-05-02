#!/bin/sh
set -eu

# simulate user capture
sudo -u $PILO_USER sh -c "echo data > $TMP/file.txt"
runuser pilo capture "$TMP/file.txt"

f="$PILO_INTAKE_PATH/file.txt"

assert_file_exists "$f"

[ "$(stat -c %U "$f")" = "$PILO_USER" ] \
    || fail "capture did not preserve user ownership"
