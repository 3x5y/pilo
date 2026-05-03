#!/bin/sh
set -eu

pile=$PILO_PILE_PATH
static=$PILO_STATIC_PATH
manifest_dir="$PILO_ADMIN_PATH"/manifest
pile_manifest="$manifest_dir"/pile.manifest
coll_manifest="$manifest_dir"/collection.manifest
filing_manifest="$manifest_dir"/filing.manifest

if [ ! -d "$manifest_dir/.git" ]
then
    as_user \
        git -c init.defaultBranch=master \
            init "$manifest_dir" >/dev/null
fi

tmp_pile=$(tmpfile)
tmp_coll=$(tmpfile)
tmp_filing=$(tmpfile)
chmod +r $tmp_pile $tmp_coll $tmp_filing
add_tmpfile_cleanup $tmp_pile $tmp_coll $tmp_filing

(
    cd $pile
    generate_manifest
) > "$tmp_pile"

(
    cd $static/collection
    generate_manifest
) > $tmp_coll

(
    cd $PILO_STATIC_PATH/filing
    generate_manifest
) > "$tmp_filing"

as_user cp $tmp_pile "$pile_manifest"
as_user git -C "$manifest_dir" add "$pile_manifest"

as_user cp $tmp_coll "$coll_manifest"
as_user git -C "$manifest_dir" add "$coll_manifest"

as_user cp "$tmp_filing" "$filing_manifest"
as_user git -C "$manifest_dir" add "$filing_manifest"

if ! as_user git -C "$manifest_dir" diff --quiet --cached
then
    as_user git -C "$manifest_dir" commit -m "manifest update" >/dev/null
fi
