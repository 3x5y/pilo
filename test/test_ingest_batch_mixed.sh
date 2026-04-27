#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
INTAKE=/tank/data/active/pile-intake

# existing canonical
echo original > /tmp/a.txt
system-capture /tmp/a.txt
system-ingest-pile

# batch intake
echo original > $INTAKE/a.txt      # idempotent
echo new > $INTAKE/b.txt           # valid
echo conflict > $INTAKE/a.txt.tmp  # conflict via rename
mv $INTAKE/a.txt.tmp $INTAKE/a.txt

capture_status system-ingest-pile

assert_command_fail

# b.txt must NOT be partially applied
assert_not_exists $PILE/in/b.txt

# canonical must remain unchanged
assert_grep original < $PILE/in/a.txt

# manifest must still verify
(cd $PILE && sha256sum --quiet --strict -c .manifest)
