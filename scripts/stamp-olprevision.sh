#!/bin/sh
# Stamp olprevision.tex (OpenLogic-Zh revision) and bdversion.tex
# (boxes-and-diamonds-zh release version from the latest tag), so
# every built PDF records which translation revision and which
# release version it corresponds to.
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

# 版本号取自最近 tag（v0.0.1 -> 0.0.1）；无 tag 时为 dev。
ver=$(git -C "$root_dir" describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || true)
ver=${ver:-dev}
printf '%% Keep the version value ASCII-safe for both pdfLaTeX and XeLaTeX.\n\\setOLBdversion{%s}%%\n' "$ver" > "$root_dir/bdversion.tex"
echo "bdversion.tex: $ver"
