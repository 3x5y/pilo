#!/bin/sh
set -e

pilo storage-snapshot-reg
pilo storage-snapshot-reg

zfs list -t snapshot -Ho name | assert_grep "-reg$"
