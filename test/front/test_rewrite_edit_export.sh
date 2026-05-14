#!/bin/sh
set -eu

mkfile a a.txt
mkfile b b.txt
capture_file a.txt
capture_file b.txt
pilo ingest-pile

OUT=$(pilo rewrite-edit --dump)

echo "$OUT" | assert_grep "^1	in/a.txt"
echo "$OUT" | assert_grep "^2	in/b.txt"
