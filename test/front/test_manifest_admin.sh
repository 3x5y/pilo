#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo ingest-pile

assert_file_exists "$PILO_ADMIN_PATH/manifest/pile.manifest"
