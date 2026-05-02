#!/bin/sh
set -eu

dataset=$PILO_PILE_DATASET
path=$PILO_PILE_PATH

with_writable $dataset \
    find "$path" -mindepth 2 -type d -empty -delete
