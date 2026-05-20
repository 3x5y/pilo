#!/usr/bin/env bash

set -euo pipefail

KEEP_EXTRA=0
TAG_PREFIX=repl-
SNAPCOLS=name,used,refer,userrefs,creation


# entry points


repl_full() {
    ! dataset_exists $TARGET_FS \
        || fatal "target $TARGET_FS exists; aborting"

    local src=$(get_source_latest)
    [ "$src" ] || fatal "unable to get latest source snapshot"

    echo == repl_full $src
    echo \# zfs hold -r $HOLD_TAG $src
    zfs hold -r $HOLD_TAG $src
    echo \# zfs send -h -R $src \
         \| zfs recv -u -o readonly=on $TARGET_FS
    zfs send -h -R $src \
        | zfs recv -u -o readonly=on $TARGET_FS
}


repl_incr() {
    zfs list $TARGET_FS >/dev/null
    local incr_src=$(get_source_latest)
    local incr_basis=$(get_incr_basis)
    [ "$incr_basis" ] || fatal "unable to get incremental basis"

    echo == repl_incr $incr_basis..$incr_src
    echo \# zfs hold -r $HOLD_TAG $incr_src
    zfs hold $HOLD_TAG $incr_src
    echo \# zfs send -h -R -I$incr_basis $incr_src \
         \| zfs recv -u -o readonly=on $TARGET_FS
    zfs send -h -R -I$incr_basis $incr_src \
        | zfs recv -u -o readonly=on $TARGET_FS
}


repl_gc() {

    report_target_snapshots
    echo == pruning $TARGET_FS
    prune_unheld $TARGET_FS
    echo

    report_target_holds
    echo == releasing target holds
    release_target_holds
    echo

    report_source_snapshots
    echo == pruning $SOURCE_FS
    prune_unheld $SOURCE_FS
    echo

    report_source_holds
    echo == releasing source holds
    release_source_holds
    echo
}


get_source_latest() {
    zfs list -t snap -s createtxg -Ho name $SOURCE_FS \
        | tail -n1
}


get_incr_basis() {
    local guid=$(zfs list -t snap -s createtxg -Ho guid $TARGET_FS \
                | tail -n1)
    zfs list -t snap -Ho name,guid $SOURCE_FS \
        | grep \\s$guid$ \
        | cut -f1
}


report_gc() {
    report_target_snapshots
    report_target_holds
    report_source_snapshots
    report_source_holds
}


prune_unheld() {
    local fs=$1
    # convert lines into comma-separated list
    local multi_line=$(get_snapshots_to_prune $fs | strip_fs)
    local single_line=$(echo $multi_line)
    local snaplist=${single_line// /,}
    if [ "$snaplist" ]
    then
        echo \# zfs destroy -v -r $fs@$snaplist
        zfs destroy -v -r $fs@$snaplist
    fi
}


get_snapshots_to_prune() {
    local fs=$1
    zfs list -t snap -Ho name,userrefs -s createtxg $fs \
        | select_oldest_unref
}


# select only the first (oldest) contiguous set of snapshots without any
# references (holds or clones)

select_oldest_unref() {
    local name refs
    while read name refs
    do
        [ "$refs" -eq 0 ] || break
        echo $name
    done
}


strip_fs() {
    local name
    while read name
    do
        echo ${name#*@}
    done
}


release_target_holds() {
    local snapshot
    get_target_holds_to_release \
    | while read snapshot
    do
        release_all_holds $snapshot
    done
}


release_all_holds() {
    local snapshot=$1
    zfs holds -Hp $snapshot | cut -f2 \
    | while read tag
    do
        release_hold $tag $snapshot
    done
}


# expired snapshots are snapshots with holds that do not have a corresponding
# snapshot on SOURCE_FS and are older than any snapshot that does exist on
# SOURCE_FS (held or not).
#
# To select them for release, iterate the oldest held snapshots on TARGET_FS
# that are not present on SOURCE_FS, stopping when, and excluding, the first
# matching snapshot found on SOURCE_FS.  These snapshots then become eligible
# for pruning by prune_unheld() the next time this process is run on the same
# TARGET_FS.

get_target_holds_to_release() {
    zfs list -t snap -s createtxg -Ho name,guid,userrefs $TARGET_FS \
        | select_held_without_source
}


# Filter for snapshots that have holds, but stop before the first snapshot that
# also exists on SOURCE_FS (matched by guid).

select_held_without_source() {
    while read name guid refs
    do
        if zfs list -t snap -Ho guid $SOURCE_FS | grep -q ^$guid$
        then
            break
        fi
        [ "$refs" -gt 0 ] || continue
        zfs holds -Hp $name | cut -f1 | sort -u
    done
}


release_source_holds() {
    get_source_holds_to_release \
    | while read snapshot
    do
        release_hold $HOLD_TAG $snapshot
    done
}


# KEEP_EXTRA + 1 to ensure we keep the most recent
get_source_holds_to_release() {
    local keep=$((KEEP_EXTRA + 1))
    zfs list -t snap -Ho name -s createtxg $SOURCE_FS \
        | xargs -r zfs holds -Hp \
        | grep "\s$HOLD_TAG\s" \
        | head -n-$keep \
        | cut -f1
}


release_hold() {
    local tag=$1
    local snapshot=$2
    echo \# zfs release -r $tag $snapshot
    zfs release -r $tag $snapshot
}


report_target_snapshots() {
    echo == target snapshots
    zfs list -t snap -o $SNAPCOLS $TARGET_FS
    echo

    echo == target snapshots to prune
    get_snapshots_to_prune $TARGET_FS \
        | xargs -r zfs list -o $SNAPCOLS
    echo
}


report_target_holds() {
    echo == target holds
    zfs list -t snap -Ho name -s createtxg $TARGET_FS \
        | xargs -r zfs holds
    echo

    echo == target holds to release
    get_target_holds_to_release | xargs -r zfs holds
    echo
}


report_source_snapshots() {
    echo == source snapshots
    zfs list -t snap -o $SNAPCOLS $SOURCE_FS
    echo

    echo == source snapshots to prune
    get_snapshots_to_prune $SOURCE_FS \
        | xargs -r zfs list -o $SNAPCOLS
    echo
}


report_source_holds() {
    echo == source holds
    zfs list -t snap -Ho name -s createtxg $SOURCE_FS \
        | xargs -r zfs holds
    echo

    echo == source holds to release
    get_source_holds_to_release \
        | xargs -r zfs holds \
        | grep -E "^NAME|\s$HOLD_TAG\s" \
        || true
    echo
}


show_count_before() {
    local source_n=$(count_snapshots $SOURCE_FS)
    local target_n=$(count_snapshots $TARGET_FS)
    local source_p=$(count_prune $SOURCE_FS)
    local target_p=$(count_prune $TARGET_FS)
    echo == gc $TARGET_ID pre: src=$source_n \
                               dst=$target_n \
                               src_prune=$source_p \
                               dst_prune=$target_p
}


show_count_after() {
    local source_n=$(count_snapshots $SOURCE_FS)
    local target_n=$(count_snapshots $TARGET_FS)
    echo == gc $TARGET_ID post: src=$source_n dst=$target_n
}


count_prune() {
    local fs=$1
    get_snapshots_to_prune $fs | wc -l
}


count_snapshots() {
    local fs=$1
    zfs list -t snap -d1 -Ho name $fs | wc -l
}


dataset_exists() {
    zfs list -t fs -H $1 &>/dev/null
}


fatal() {
    echo "$@" 1>&2
    exit 1
}


usage() {
    echo Usage:
    echo $0 CMD
    echo
    echo Commands:
    echo
    echo "  full   SOURCE TARGET TAG"
    echo "  incr   SOURCE TARGET TAG"
    echo "  gc     SOURCE TARGET TAG"
    echo "  report SOURCE TARGET TAG"
    echo
}


cmd_config() {
    SOURCE_FS=$1
    TARGET_FS=$2
    TARGET_ID=$3
    HOLD_TAG=$TAG_PREFIX$TARGET_ID
    # check source exists
    zfs list $SOURCE_FS >/dev/null
}


if [ $# -ge 1 ]
then
    cmd=$1
    shift
else
    cmd=help
fi


case $cmd in
    full)
        cmd_config "$@"
        repl_full
        ;;
    incr)
        cmd_config "$@"
        repl_incr
        ;;
    report)
        cmd_config "$@"
        report_gc
        ;;
    gc)
        cmd_config "$@"
        repl_gc
        ;;
    help)
        usage
        ;;
esac
