#!/bin/sh
set -e

PILE=/tank/data/active/pile
FILE=test.txt

echo valid > /tmp/$FILE
system-capture /tmp/$FILE
system-ingest-pile

system-manifest-update

system-manifest-verify
