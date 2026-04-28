#!/bin/sh
set -e

one=a/1.txt
two=b/2.txt
mkintake one $one
mkintake two $two

system-ingest-pile

assert_file_exists /$PILE/in/$one
assert_file_exists /$PILE/in/$two
