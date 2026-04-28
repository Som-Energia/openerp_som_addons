#!/bin/bash
set -euo pipefail

REPO="${WEBCLIENT_REPO:-gisce/webclient}"
HTML_DIR="${HTML_DIR:-/usr/share/nginx/html}"
STATE_FILE="${STATE_FILE:-/var/lib/webclient/current_tag}"

mkdir -p "$(dirname "$STATE_FILE")" "$HTML_DIR"

auth=()
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    auth=(-H "Authorization: Bearer $GITHUB_TOKEN")
fi

release_json=$(curl -fsSL "${auth[@]}" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/$REPO/releases/latest")

tag=$(echo "$release_json" | jq -r '.tag_name')
zip_url=$(echo "$release_json" \
    | jq -r '.assets[] | select(.name | endswith(".zip")) | .url' \
    | head -n1)

if [[ -z "$tag" || "$tag" == "null" ]]; then
    echo "[update-webclient] Could not read tag_name from GitHub response" >&2
    exit 1
fi
if [[ -z "$zip_url" || "$zip_url" == "null" ]]; then
    echo "[update-webclient] No .zip asset in release $tag" >&2
    exit 1
fi

current_tag=""
[[ -f "$STATE_FILE" ]] && current_tag=$(cat "$STATE_FILE")

if [[ "$current_tag" == "$tag" ]]; then
    echo "[update-webclient] Already at $tag"
    exit 0
fi

echo "[update-webclient] Updating ${current_tag:-<none>} -> $tag"

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

curl -fsSL "${auth[@]}" \
    -H "Accept: application/octet-stream" \
    -o "$tmp_dir/webclient.zip" "$zip_url"
mkdir -p "$tmp_dir/extracted"
unzip -q "$tmp_dir/webclient.zip" -d "$tmp_dir/extracted"

shopt -s nullglob
entries=("$tmp_dir/extracted"/*)
shopt -u nullglob
if [[ ${#entries[@]} -eq 1 && -d "${entries[0]}" ]]; then
    src_dir="${entries[0]}"
else
    src_dir="$tmp_dir/extracted"
fi

if [[ ! -f "$src_dir/index.html" ]]; then
    echo "[update-webclient] No index.html found after unzip, aborting" >&2
    exit 1
fi

rm -rf "${HTML_DIR:?}"/* "${HTML_DIR:?}"/.[!.]* 2>/dev/null || true
shopt -s dotglob
cp -a "$src_dir"/* "$HTML_DIR/"
shopt -u dotglob

echo "$tag" > "$STATE_FILE"
echo "[update-webclient] Installed $tag"
