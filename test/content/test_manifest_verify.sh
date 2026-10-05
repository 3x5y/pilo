#!/bin/sh
set -e

echo valid > /$PILE/in/foo.txt
create_pile_manifest

capture_status pilo manifest-verify
assert_command_ok manifest did not verify
