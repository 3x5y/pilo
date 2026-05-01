#!/bin/sh
set -e

mkfile valid foo.txt
pilo-ingest-pile

pilo-manifest-update

pilo-manifest-verify
