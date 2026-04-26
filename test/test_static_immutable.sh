#!/bin/sh
set -e

system-init

FILE=file.txt
echo important > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

# attempt modification after promotion
if (echo tamper >> /$TEST_ROOT/static/$FILE) 2>/dev/null
then
    fail file writable after promotion
fi
