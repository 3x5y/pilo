#!/bin/sh
set -eu

TEST_SKIP=1

mkfile data file.txt
capture_file file.txt
pilo content-ingest

assert_dir_exists /"$ADMIN"/manifest/.git
