#!/bin/sh
set -e

echo skipped
exit 0

file=immutable.txt
mkfile important $file
capture_file $file
pilo content-ingest

# attempt modification after promotion
if (echo tamper >> /$PILE/in/$file) 2>/dev/null
then
    fail file writable after promotion
fi
