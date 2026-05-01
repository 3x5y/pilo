#!/bin/sh
set -e

pilo snapshot-anchor
pilo snapshot-rpo

zfs list -t snapshot | assert_grep "@a-"
zfs list -t snapshot | assert_grep "@r-"
