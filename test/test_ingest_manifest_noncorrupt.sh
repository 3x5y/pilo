#!/bin/sh
set -e

PILE=/tank/data/active/pile-readonly

echo good > /tmp/a.txt
echo good > /tmp/b.txt

system-capture /tmp/a.txt
system-capture /tmp/b.txt
system-ingest-pile

# introduce conflict for b.txt
echo bad > /tank/data/active/pile-intake/b.txt

capture_status system-ingest-pile
assert_command_fail

# manifest must still be valid
(cd $PILE && sha256sum --quiet --strict -c .manifest)

# and still reflect original state
assert_grep good < $PILE/b.txt
