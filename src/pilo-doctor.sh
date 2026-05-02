#!/bin/sh
set -eu

require_dataset "$PILO_ADMIN_DATASET"
require_dataset "$PILO_INTAKE_DATASET"
require_dataset "$PILO_PILE_DATASET"
require_dataset "$PILO_COLLECTION_DATASET"
