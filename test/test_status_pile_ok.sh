#!/bin/sh
set -e

FILE=new_file.txt

# new file
echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

capture_status system-status pile

[ $STATUS -eq 0 ] || fail expected no pile age warning
