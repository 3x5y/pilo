#!/bin/sh
set -eu

mkfile data file.txt
capture_file file.txt
pilo content-ingest

assert_dir_exists /"$ADMIN"/manifest/.git
