#!/bin/sh
set -eu

mkfile a a.txt
mkfile b b.txt
capture_file a.txt
capture_file b.txt
pilo content-ingest

capture_status pilo content-reorg-edit --script <<EOF
1	in/x.txt
2	in/x.txt
EOF

assert_command_fail
echo "$OUTPUT" | assert_grep "duplicate"
