#!/bin/sh
set -e

pilo snapshot-reg
pilo snapshot-reg

zfs list -t snapshot -Ho name | assert_grep "-reg$"
