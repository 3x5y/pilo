#!/bin/sh
set -eu

mkfile data file.txt

# simulate user capture
runuser pilo capture "$TMP/file.txt"

f="$PILO_INTAKE_PATH/file.txt"
assert_file_exists "$f"
assert_owner $PILO_USER $f
