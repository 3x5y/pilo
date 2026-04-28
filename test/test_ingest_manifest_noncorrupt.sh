#!/bin/sh
set -e

mkfile good a.txt
capture_file a.txt
mkfile good b.txt
capture_file b.txt
system-ingest-pile
# introduce conflict for b.txt
mkintake bad b.txt

capture_status system-ingest-pile
assert_command_fail

# manifest must still be valid
assert_manifest_valid /$PILE

# and still reflect original state
assert_grep good < /$PILE/in/b.txt
