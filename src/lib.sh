
require_arg() {
    [ -n "${1:-}" ] || die "missing argument: $2"
}

fatal() {
    echo "ERROR: $*" >&2
    exit 1
}

tmpfile() {
    local f=$(mktemp /tmp/pilo-tmp-XXXXXXXX)
    echo "$f"
}

cleanup() {
    rm -f /tmp/pilo-tmp-*
}

trap cleanup EXIT

dataset_exists() {
    zfs list "$1" >/dev/null 2>&1
}

require_dataset() {
    if ! dataset_exists "$1"
    then
        echo "ERROR: missing required dataset: $1"
        return 1
    fi
}

dir_exists() {
    [ -d "$1" ]
}

require_dir() {
    if ! dir_exists "$1"
    then
        echo "ERROR: path does not exist: $1"
        return 1
    fi
}

ensure_dir() {
    dir_exists "$1" || mkdir -p "$1"
}

with_writable() {
    local dataset=$1
    shift
    zfs set readonly=off $dataset
    set +e
    "$@"
    local result=$?
    set -e
    zfs set readonly=on $dataset
    return $result
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
