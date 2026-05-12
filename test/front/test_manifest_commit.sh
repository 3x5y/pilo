#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

cd "$PILO_ADMIN_PATH"/manifest
runuser git log --oneline | assert_grep "manifest update"
