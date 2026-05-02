#!/bin/sh
set -eu

dataset=$PILO_INTAKE_DATASET

require_dataset "$dataset"

cp -a "$1" $PILO_INTAKE_PATH/
