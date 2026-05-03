#!/bin/sh
set -eu

pile=$PILO_PILE_PATH
manifest_dir="$PILO_ADMIN_PATH"/manifest
manifest="$manifest_dir"/pile.manifest

tmp=$(tmpfile)
chmod +r $tmp

require_dir "$pile"
cd $pile
generate_manifest > "$tmp"

if [ ! -d "$manifest_dir/.git" ]
then
    as_user \
        git -c init.defaultBranch=master \
        init "$manifest_dir" >/dev/null
fi

as_user cp $tmp "$manifest"
as_user git -C "$manifest_dir" add "$manifest"
if ! as_user git -C "$manifest_dir" diff --quiet --cached
then
    as_user git -C "$manifest_dir" commit -m "manifest update" >/dev/null
fi
