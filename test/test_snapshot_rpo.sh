#!/bin/sh
set -e

system-snapshot-rpo

zfs list -t snapshot | assert_grep "@r-"
