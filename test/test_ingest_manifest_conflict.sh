#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly
FILE=file.txt

echo original > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

# conflicting intake
echo different > /tank/data/active/pile-intake/$FILE

capture_status system-ingest-pile

assert_command_fail expected checksum conflict
echo "$OUTPUT" | assert_grep "collision"

# manifest still valid
(cd $PILE && sha256sum --quiet --strict -c .manifest)

# canonical unchanged
assert_grep original < $PILE/$FILE
