#!/bin/sh
set -eu

mkfile data a.txt
capture_file a.txt
pilo content-ingest

repo="$PILO_ADMIN_PATH/manifest"
assert_command_ok git -C "$repo" rev-parse HEAD
runuser git -C "$repo" ls-files | assert_grep "pile.manifest"
#runuser git -C "$repo" ls-files | assert_grep "collection.manifest"
#runuser git -C "$repo" ls-files | assert_grep "filing.manifest"
