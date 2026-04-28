#!/bin/sh
set -e

file=foo/file.txt
mkintake data $file

system-ingest-pile

assert_file_exists /$PILE/in/$file
