#!/bin/sh
set -eu

mkfile a a.txt
capture_file a.txt

pilo content-ingest

script=$(printf "rm\tin/a.txt")

OUT=$(pilo rewrite --preview "$script")

echo "$OUT" | assert_grep "unlink"
