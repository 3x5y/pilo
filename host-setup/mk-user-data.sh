NAME=pi10

ssh-keygen -t ed25519 -f "$NAME"_host_key -N '' -C "$NAME":host
export SSH_HOST_KEY_PRIVATE=$(sed 's/^/    /' "$NAME"_host_key )
export SSH_HOST_KEY_PUBLIC=$(< "$NAME"_host_key.pub )
ssh-keygen -t ed25519 -f "$NAME"_user_key -N '' -C "$NAME":user
export USER_SSH_KEY=$(< "$NAME"_user_key.pub )
export USER_PASSWD=$(mkpasswd)
envsubst < user-data.template > user-data

echo 192.168.1.10 $(cut -d' ' -f1,2 "$NAME"_host_key.pub) > "$NAME"_known_hosts
