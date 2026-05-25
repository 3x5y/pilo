#!/bin/sh
set -eu

mkintake "A" a.txt
mkintake "B" b.txt

pilo content-ingest   # first pass succeeds

# introduce conflict for second run
mkintake "DIFF" a.txt

capture_status pilo content-ingest
assert_command_fail

# ensure conflicting file still in intake
assert_file_exists "$PILO_INTAKE_PATH/a.txt"

# ensure existing pile file untouched
assert_file_exists "$PILO_PILE_PATH/in/a.txt"
