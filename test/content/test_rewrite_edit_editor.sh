#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt
pilo content-ingest

export EDITOR="sed -i s/a/b/"

pilo content-reorg-edit

assert_file_exists "$PILO_PILE_PATH/in/b.txt"
