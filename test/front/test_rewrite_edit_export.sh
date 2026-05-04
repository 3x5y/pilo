#!/bin/sh
set -eu

mkfile a a.txt
mkfile b b.txt
capture_file a.txt
capture_file b.txt
pilo ingest-pile

OUT=$(pilo rewrite-edit --dump)

echo "$OUT" | assert_grep "in/a.txt"
echo "$OUT" | assert_grep "in/b.txt"
