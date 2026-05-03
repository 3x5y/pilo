
require_arg() {
    [ -n "${1:-}" ] || fatal "missing argument: $2"
}

error() {
    echo "ERROR: $*" >&2
}

fatal() {
    error "$@"
    exit 1
}

CLEANUP_TMPFILES=""
CLEANUP_DATASETS=""

general_cleanup() {
    for f in $CLEANUP_TMPFILES
    do
        rm -f $f
    done
    for ds in $CLEANUP_DATASETS
    do
        zfs set readonly=on $ds
    done
}

trap general_cleanup EXIT

add_tmpfile_cleanup() {
    CLEANUP_TMPFILES="$CLEANUP_TMPFILES $*"
}

add_dataset_cleanup() {
    CLEANUP_DATASETS="$CLEANUP_DATASETS $*"
}

tmpfile() {
    local f=$(mktemp /tmp/pilo.XXXXXXXX)
    echo "$f"
}

as_user() {
    if [ "$(id -un)" = "$PILO_USER" ]
    then
        "$@"
    else
        sudo -u "$PILO_USER" "$@"
    fi
}

dataset_exists() {
    zfs list "$1" >/dev/null 2>&1
}

require_dataset() {
    dataset_exists "$1" || fatal "missing required dataset: $1"
}

dir_exists() {
    [ -d "$1" ]
}

file_exists() {
    [ -f "$1" ]
}

require_dir() {
    dir_exists "$1" || fatal "path does not exist: $1"
}

ensure_dir() {
    dir_exists "$1" || as_user mkdir -p "$1"
}

with_writable() {
    local dataset=$1
    shift
    zfs set readonly=off $dataset
    add_dataset_cleanup "$dataset"
    set +e
    "$@"
    local result=$?
    set -e
    zfs set readonly=on $dataset
    return $result
}

get_readonly() {
    zfs get -H -o value readonly "$1"
}

snapshot_timestamp() {
    date +%Y%m%d_%H%M%S_%N
}

snapshot() {
    local name=$1
    local dataset=${2:-}
    [ "$dataset" ] || dataset="$PILO_ROOT"
    zfs snapshot -r "$dataset@$name"
}

get_latest_guid() {
    zfs list -t snapshot -Ho guid -s creation "$1" | tail -n1
}

generate_manifest() {
    find . -type f ! -name .manifest -print0 \
        | LC_COLLATE=C sort -z \
        | xargs -r0 sha256sum
}
