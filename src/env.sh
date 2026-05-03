
: "${PILO_ROOT:?PILO_ROOT not set}"
: "${PILO_PATH:?PILO_PATH not set}"
: "${PILO_USER:?PILO_USER not set}"

export PILO_ACTIVE_DATASET="$PILO_ROOT/active"
export PILO_ADMIN_DATASET="$PILO_ROOT/active/admin"
export PILO_INTAKE_DATASET="$PILO_ROOT/active/pile-intake"
export PILO_PILE_DATASET="$PILO_ROOT/active/pile-readonly"
export PILO_STASH_DATASET="$PILO_ROOT/stash"
export PILO_STATIC_DATASET="$PILO_ROOT/static"
export PILO_COLLECTION_DATASET="$PILO_ROOT/static/collection"
export PILO_FILING_DATASET="$PILO_ROOT/static/filing"
export PILO_ADMIN_PATH="$PILO_PATH/active/admin"
export PILO_INTAKE_PATH="$PILO_PATH/active/pile-intake"
export PILO_PILE_PATH="$PILO_PATH/active/pile-readonly"
export PILO_STATIC_PATH="$PILO_PATH/static"

