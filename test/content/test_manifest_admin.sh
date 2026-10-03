#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo content-ingest

assert_file_exists /"$ADMIN/manifest/pile.manifest"
assert_owner $PILO_USER /"$ADMIN"/manifest/.git
