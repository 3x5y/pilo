#!/bin/sh
set -e

# existing canonical
mkfile original a.txt
capture_file a.txt
system-ingest-pile

# batch intake
mkintake original a.txt     # idempotent
mkintake new b.txt          # valid
mkintake conflict a.txt.tmp # conflict via rename
mv /$INTAKE/a.txt.tmp /$INTAKE/a.txt

capture_status system-ingest-pile

assert_command_fail

# b.txt must NOT be partially applied
assert_not_exists /$PILE/in/b.txt

# canonical must remain unchanged
assert_grep original < /$PILE/in/a.txt

# manifest must still verify
(cd /$PILE && sha256sum --quiet --strict -c .manifest)
