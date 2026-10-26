#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

image=${1:?Usage: deploy.sh IMAGE COMMIT_SHA}
tag=${2:?Usage: deploy.sh IMAGE COMMIT_SHA}
[[ $image =~ ^ghcr\.io/[a-z0-9._/-]+$ && $tag =~ ^[a-f0-9]{40}$ ]] || exit 2
root=${STIMULUS_ROOT:-/opt/stimulus}
release=$(cd -- "$(dirname -- "$0")/.." && pwd)
export STIMULUS_SHARED_DIR="$root/shared"
[[ -f $STIMULUS_SHARED_DIR/.env && -d $root/releases && -d $root/backups ]]
exec 9>"$root/deploy.lock"
flock -n 9 || { echo 'Another deployment is running' >&2; exit 1; }
[[ $(readlink -f "$root/current" || true) != "$release" ]] || {
    echo 'This release is already current; use a new release directory' >&2; exit 1;
}
printf 'APP_IMAGE=%s\nIMAGE_TAG=%s\n' "$image" "$tag" > "$release/image.env"

compose() (
    local directory=$1
    shift
    set -a
    source "$directory/image.env"
    set +a
    docker compose --project-name stimulus --project-directory "$directory" \
        --env-file "$STIMULUS_SHARED_DIR/.env" -f "$directory/compose.yaml" "$@"
)
start_release() {
    compose "$1" up -d || return
    # Проверяем готовность при запуске отдельно от часового Docker healthcheck.
    curl --fail --silent --show-error --max-time 3 \
        --retry 60 --retry-all-errors --retry-delay 2 --retry-max-time 120 \
        http://127.0.0.1:8000/healthz > /dev/null
}
compose "$release" config --quiet
compose "$release" pull
previous=""
if [[ -L $root/current ]]; then
    previous=$(readlink -f "$root/current")
fi
stopped=false
rollback() {
    local status=$?
    trap - EXIT
    if (( status != 0 )) && $stopped; then
        echo 'Deployment failed; restoring the previous release' >&2
        if [[ -n $previous && -f $previous/image.env ]]; then
            start_release "$previous" || \
                echo 'ROLLBACK FAILED: inspect container logs and backups' >&2
        else
            compose "$release" stop || true
            echo 'No previous release exists; initial deployment failed' >&2
        fi
    fi
    exit "$status"
}
trap rollback EXIT
# Останавливаем и на первом деплое: SQLite и фотографии копируются без конкурентной записи.
stopped=true
if [[ -n $previous && -f $previous/image.env ]]; then
    compose "$previous" stop
else
    compose "$release" stop
fi
backup="$root/backups/$(date -u +%Y%m%dT%H%M%S)-$tag-$$.tar.gz"
# tar внутри helper-контейнера читает файлы UID 10001, даже с режимом 600.
docker run --rm --user 10001:10001 --entrypoint tar \
    --mount "type=bind,src=$STIMULUS_SHARED_DIR,dst=/backup,readonly" \
    "$image:$tag" -C /backup -czf - data uploads > "$backup"
cp "$STIMULUS_SHARED_DIR/.env" "$backup.env"
if [[ -n $previous && -f $previous/image.env ]]; then
    cp "$previous/image.env" "$backup.image.env"
fi
start_release "$release"
curl --fail --silent --show-error --max-time 10 http://127.0.0.1:8000/ > /dev/null
if [[ -n $previous ]]; then
    ln -sfn "$previous" "$root/previous.next"
    mv -Tf "$root/previous.next" "$root/previous"
fi
ln -sfn "$release" "$root/current.next"
mv -Tf "$root/current.next" "$root/current"
stopped=false
echo "Deployed $image:$tag; backup: $backup"
