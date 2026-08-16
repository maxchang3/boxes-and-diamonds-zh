#!/bin/sh
# Stamp olprevision.tex (OpenLogic-Zh revision) and bdversion.tex
# (boxes-and-diamonds-zh release version), so every built PDF records
# which translation revision and which release version it corresponds
# to.
#
# 版本号取 release-please manifest（.release-please-manifest.json，仓库
# 跟踪文件：release PR 合并时已更新为即将发布的版本——CI 在 release-please
# 打 tag 之前构建，git describe 会取到上一个 tag，导致 release 附件滞后
# 一版）。manifest 是跟踪文件，必然存在；读取失败才回退 dev。
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

ver=$(python3 -c "import json; print(json.load(open('$root_dir/.release-please-manifest.json'))['.'])" 2>/dev/null || true)
ver=${ver:-dev}
printf '%% Keep the version value ASCII-safe for both pdfLaTeX and XeLaTeX.\n\\setOLBdversion{%s}%%\n' "$ver" > "$root_dir/bdversion.tex"
echo "bdversion.tex: $ver"
