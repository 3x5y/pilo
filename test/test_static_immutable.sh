#!/bin/sh
set -e

file=immutable.txt
mkfile important $file
capture_file $file
system-ingest-pile

# attempt modification after promotion
if (echo tamper >> /$PILE/in/$file) 2>/dev/null
then
    fail file writable after promotion
fi
