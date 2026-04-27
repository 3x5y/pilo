#!/bin/sh
set -e

FILE=file.txt

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

system-static-promote $FILE collection

echo data > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

system-static-promote $FILE collection

assert_file_exists /tank/data/static/collection/$FILE
assert_not_exists /tank/data/active/pile-readonly/$FILE
