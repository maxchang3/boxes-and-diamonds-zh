#!/bin/sh
# Stamp olprevision.tex (OpenLogic-Zh revision) and bdversion.tex
# (boxes-and-diamonds-zh release version), so every built PDF records
# which translation revision and which release version it corresponds
# to.
#
# 版本号优先取 release-please manifest（.release-please-manifest.json，
# release PR 合并时已更新为即将发布的版本——CI 在 release-please 打 tag
# 之前构建，git describe 会取到上一个 tag，导致 release 附件滞后一版）；
# 无 manifest 时退回最近 tag（v0.0.1 -> 0.0.1）；都没有时为 dev。
#
# Usage: sh scripts/stamp-olprevision.sh [OLP_DIR]
#   OLP_DIR defaults to ../OpenLogic-Zh (sibling checkout).
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
olp_dir=${1:-"$root_dir/../OpenLogic-Zh"}

test -d "$olp_dir/.git" || {
  echo "missing OpenLogic-Zh checkout: $olp_dir" >&2
  exit 1
}

# Keep the shared revision value ASCII-safe for both pdfLaTeX and XeLaTeX.
rev=$(git -C "$olp_dir" rev-parse --short HEAD)
date=$(git -C "$olp_dir" log -1 --format=%cs)
printf '%% Keep the shared revision value ASCII-safe for both pdfLaTeX and XeLaTeX.\n\\setOLPrevision{%s (%s)}%%\n' "$rev" "$date" > "$root_dir/olprevision.tex"
echo "olprevision.tex: $rev ($date)"

ver=""
if [ -f "$root_dir/.release-please-manifest.json" ]; then
  ver=$(python3 -c "import json; print(json.load(open('$root_dir/.release-please-manifest.json'))['.'])" 2>/dev/null || true)
fi
if [ -z "$ver" ]; then
  ver=$(git -C "$root_dir" describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || true)
fi
ver=${ver:-dev}
printf '%% Keep the version value ASCII-safe for both pdfLaTeX and XeLaTeX.\n\\setOLBdversion{%s}%%\n' "$ver" > "$root_dir/bdversion.tex"
echo "bdversion.tex: $ver"
