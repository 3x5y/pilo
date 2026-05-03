#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

pilo manifest-update

assert_file_exists "$PILO_ADMIN_PATH/manifest/pile.manifest"
#assert_not_exists "$PILO_PILE_PATH/.manifest"
