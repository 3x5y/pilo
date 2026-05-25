#!/bin/sh
set -e

file=foo/file.txt
mkintake data $file

pilo content-ingest

assert_file_exists /$PILE/in/$file
