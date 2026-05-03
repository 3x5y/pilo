#!/bin/sh
set -eu

pile=$PILO_PILE_PATH

tmp=$(tmpfile)
chmod +r $tmp

require_dir "$pile"
cd $pile
generate_manifest > "$tmp"

as_user mkdir -p "$PILO_ADMIN_PATH"/manifest
if [ ! -d "$PILO_ADMIN_PATH/.git" ]
then
    git -c init.defaultBranch=master \
        init "$PILO_ADMIN_PATH" >/dev/null
fi
as_user cp $tmp "$PILO_ADMIN_PATH"/manifest/pile.manifest
