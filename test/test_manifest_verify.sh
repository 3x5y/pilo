#!/bin/sh
set -e

mkfile valid foo.txt
system-ingest-pile

system-manifest-update

system-manifest-verify
