#!/usr/bin/env bash
set -Eeuo pipefail

readonly LOCKFILE=/run/lock/pilo-storage.lock
readonly ROTATION_DIR=/var/lib/pilo/rotation
readonly ROTATION_MARKER="${ROTATION_DIR}/pending"

HERE=$(dirname $(readlink -f $0))
CONFIG=$HERE/../pilo.conf.sh
. "$CONFIG"

phase=starting

log() {
    #logger -t pilo-prerotate -- "$*"
    echo "$*"
}

fail() {
    log "Aborted: phase=${phase}: $*"
    printf 'pilo-prerotate: %s\n' "$*" >&2
    exit 1
}

exec 9> "$LOCKFILE"

if ! flock -n 9
then
    fail "another storage operation is active"
fi

if [[ -e "$ROTATION_MARKER" ]]
then
    fail "rotation is already pending; inspect the existing rotation"
fi

report_fail() {
    rc=$?
    if (( rc != 0 ))
    then
        log "Failed: phase=${phase}, exit_code=${rc}"
    fi
}

trap report_fail EXIT

phase=validate-topology
log "Validating storage topology"
pilo status replication

phase=snapshot
log "Creating primary snapshot"
pilo storage-snapshot-mark

phase=replicate
log "Replicating to secondary"
pilo storage-replicate-safe

phase=verify-replication
log "Verifying replication convergence"
pilo storage-replication-verify

phase=create-marker
log "Recording pending rotation"

# Create the marker atomically. Keep the temporary file in the same
# directory so the final rename is atomic.
tmp=$(mktemp "${ROTATION_DIR}/.pending.XXXXXX")
printf 'started_at=%s\n' "$(date --iso-8601=seconds)" > "$tmp"
mv -T "$tmp" "$ROTATION_MARKER"

phase=export-secondary
log "Exporting secondary pool"
#pilo storage-secondary-export
# Must export the one attached secondary pool, not the primary pool.
for ds in $PILO_SECONDARY_ROOTS
do
    sec=${ds%%/*}
    if zpool status $sec &> /dev/null
    then
        zpool export $sec
        break
    fi
done

phase=complete
log "Pre-rotation completed; secondary may now be physically removed"
