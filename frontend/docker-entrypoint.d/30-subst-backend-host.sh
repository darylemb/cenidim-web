#!/bin/sh
# Substitute ${CENIDIM_BACKEND_HOST} in the nginx config at startup.
# The nginx-unprivileged image runs every shell script in
# /docker-entrypoint.d/ before nginx itself, so we can rewrite the
# config in place. envsubst is provided by the base image's gettext
# package.
set -eu

CONFIG=/etc/nginx/conf.d/default.conf
if [ -z "${CENIDIM_BACKEND_HOST:-}" ]; then
    echo "[entrypoint] CENIDIM_BACKEND_HOST not set; defaulting to 'backend'" >&2
    export CENIDIM_BACKEND_HOST=backend
fi

envsubst '${CENIDIM_BACKEND_HOST}' < "$CONFIG" > "${CONFIG}.tmp"
mv "${CONFIG}.tmp" "$CONFIG"
echo "[entrypoint] nginx upstream set to http://${CENIDIM_BACKEND_HOST}:8000" >&2