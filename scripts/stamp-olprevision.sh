#!/bin/sh
# Stamp olprevision.tex with the actually-checked-out OpenLogic-Zh
# revision, so every built PDF records which upstream revision its
# Chinese translation corresponds to.
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
