#!/bin/sh
set -e

pilo snapshot-incr
pilo snapshot-incr

zfs list -t snapshot -Ho name | assert_grep "-incr$"
