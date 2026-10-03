#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo content-ingest

cd /"$ADMIN"/manifest
runuser git log --oneline | assert_grep "manifest update"
