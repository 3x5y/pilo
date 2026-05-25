#!/bin/sh
set -e

mkfile valid foo.txt
pilo content-ingest

pilo manifest-verify
