#!/bin/sh
set -e

pilo snapshot-rpo

zfs list -t snapshot | assert_grep "@r-"
