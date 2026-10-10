#!/usr/bin/env bash
set -Eeuo pipefail

readonly LOCKFILE=/run/lock/pilo.lock
readonly STATE_DIR=/var/lib/pilo/status
readonly TRIGGER=/var/lib/pilo/request/cycle
readonly LAST_CYCLE="${STATE_DIR}/last-cycle"
readonly ROTATION_MARKER=/var/lib/pilo/rotation/pending

exec 9> "$LOCKFILE"

if ! flock -n 9
then
    logger -t pilo-cycle "Skipped: another storage operation is active"
    exit 0
fi

phase=starting
started_at=$(date --iso-8601=seconds)

write_result() {
    local rc=$?
    local finished_at
    local result
    local tmp

    trap - EXIT
    finished_at=$(date --iso-8601=seconds)

    if (( rc == 0 ))
    then
        result=success
    else
        result=failure
    fi

    printf '%s\n' \
        "started_at=${started_at}" \
        "finished_at=${finished_at}" \
        "result=${result}" \
        "exit_code=${rc}" \
        "phase=${phase}" \
        > "${LAST_CYCLE}.tmp" || true

    if [[ -f "${LAST_CYCLE}.tmp" ]]
    then
        mv -f "${LAST_CYCLE}.tmp" "${LAST_CYCLE}" || true
    fi

    if (( rc == 0 ))
    then
        logger -t pilo-cycle "Cycle succeeded"
    else
        logger -t pilo-cycle \
            "Cycle failed: phase=${phase}, exit_code=${rc}"
    fi

    exit "${rc}"
}

trap write_result EXIT

echo 'PILO cycle started:' "${started_at}"

# Requests are best-effort and may coalesce.
# Consume any pending request when this run begins.
phase=consume-request
rm -f "${TRIGGER}"

# Create a new primary snapshot.
phase=snapshot
echo 'SNAPSHOT'
pilo storage-snapshot-reg

# Rotation deliberately pauses replication, not snapshot creation.
if [[ -e "$ROTATION_MARKER" ]]
then
    phase=replication-paused
    echo 'Rotation pending; skipping replication'
    exit 0
fi

# Replicate to the attached secondary, if one is available.
phase=replicate
echo 'REPLICATE'
pilo storage-replicate-safe

# Require the replication postcondition to hold.
phase=verify-replication
echo 'VERIFY REPLICATION'
pilo storage-replication-verify

# Report final system status.
phase=verify-status
echo 'VERIFY STATUS'
pilo status

phase=complete
echo 'PILO cycle completed successfully'

