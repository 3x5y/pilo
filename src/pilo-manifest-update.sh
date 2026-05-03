#!/bin/sh
set -eu

pile=$PILO_PILE_PATH
static=$PILO_STATIC_PATH
manifest_dir="$PILO_ADMIN_PATH"/manifest
pile_manifest="$manifest_dir"/pile.manifest
coll_manifest="$manifest_dir"/collection.manifest

if [ ! -d "$manifest_dir/.git" ]
then
    as_user \
        git -c init.defaultBranch=master \
            init "$manifest_dir" >/dev/null
fi

tmp_pile=$(tmpfile)
tmp_coll=$(tmpfile)
chmod +r $tmp_pile $tmp_coll
add_tmpfile_cleanup $tmp_pile $tmp_coll

(
    cd $pile
    generate_manifest
) > "$tmp_pile"

(
    cd $static/collection
    generate_manifest
) > $tmp_coll

as_user cp $tmp_pile "$pile_manifest"
as_user git -C "$manifest_dir" add "$pile_manifest"

as_user cp $tmp_coll "$coll_manifest"
as_user git -C "$manifest_dir" add "$coll_manifest"

if ! as_user git -C "$manifest_dir" diff --quiet --cached
then
    as_user git -C "$manifest_dir" commit -m "manifest update" >/dev/null
fi
