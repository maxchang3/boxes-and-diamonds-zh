#!/bin/sh
# Usage: sh scripts/stamp-olprevision.sh [OLP_DIR]
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
olp_dir=${1:-"$root_dir/../OpenLogic-Zh"}

test -d "$olp_dir/.git" || {
  echo "missing OpenLogic-Zh checkout: $olp_dir" >&2
  exit 1
}

rev=$(git -C "$olp_dir" rev-parse --short HEAD)
date=$(git -C "$olp_dir" log -1 --format=%cs)
printf '\\setOLPrevision{%s (%s)}%%\n' "$rev" "$date" > "$root_dir/olprevision.tex"
echo "olprevision.tex: $rev ($date)"

# release PR 合并后的构建早于打 tag，因此版本取 manifest。
ver=$(python3 -c "import json; print(json.load(open('$root_dir/.release-please-manifest.json'))['.'])" 2>/dev/null || true)
ver=${ver:-dev}
printf '\\setOLBdversion{%s}%%\n' "$ver" > "$root_dir/bdversion.tex"
echo "bdversion.tex: $ver"
