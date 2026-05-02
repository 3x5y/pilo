
: "${PILO_ROOT:?PILO_ROOT not set}"
: "${PILO_PATH:?PILO_PATH not set}"

PILO_ACTIVE_DATASET="$PILO_ROOT/active"
PILO_ADMIN_DATASET="$PILO_ROOT/active/admin"
PILO_INTAKE_DATASET="$PILO_ROOT/active/pile-intake"
PILO_PILE_DATASET="$PILO_ROOT/active/pile-readonly"
PILO_STASH_DATASET="$PILO_ROOT/stash"
PILO_STATIC_DATASET="$PILO_ROOT/static"
PILO_COLLECTION_DATASET="$PILO_ROOT/static/col"
PILO_FILING_DATASET="$PILO_ROOT/static/fil"

: "${PILO_ADMIN_PATH:=$PILO_PATH/active/admin}"
: "${PILO_INTAKE_PATH:=$PILO_PATH/active/pile-intake}"
: "${PILO_PILE_PATH:=$PILO_PATH/active/pile-readonly}"
: "${PILO_STATIC_PATH:=$PILO_PATH/static}"
