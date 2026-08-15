#!/bin/sh
# Deterministic post-build checks for B&D PDFs.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root_dir=$(CDPATH= cd -- "$script_dir/.." && pwd)
target=${1:-}

case "$target" in
  zh-bd-screen|zh-bd-print|bd-screen) : ;;
  *)
    echo "usage: $0 zh-bd-screen|zh-bd-print|bd-screen" >&2
    exit 2
    ;;
esac

cd "$root_dir"
pdf="$target.pdf"
log="$target.log"

test -d ../OpenLogic-Zh || {
  echo "missing sibling repository: ../OpenLogic-Zh" >&2
  exit 1
}
test -f "$pdf" || {
  echo "missing build output: $pdf (run make $target first)" >&2
  exit 1
}
test -f "$log" || {
  echo "missing build log: $log" >&2
  exit 1
}

if grep -n -E '^!|Undefined control sequence|Token .*undefined' "$log"; then
  echo "TeX errors or undefined tokens found in $log" >&2
  exit 1
fi

command -v pdftotext >/dev/null 2>&1 || {
  echo "pdftotext is required for the PDF text check" >&2
  exit 1
}

tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/bd-build-check.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM
pdftotext "$pdf" "$tmp_dir/text.txt"

if [ "$target" = zh-bd-screen ] || [ "$target" = zh-bd-print ]; then
  grep -q '盒子与钻石' "$tmp_dir/text.txt" || {
    echo "Chinese title not found in $pdf" >&2
    exit 1
  }
  grep -q '模态逻辑' "$tmp_dir/text.txt" || {
    echo "Chinese body text not found in $pdf" >&2
    exit 1
  }
else
  grep -q 'Boxes and Diamonds' "$tmp_dir/text.txt" || {
    echo "English title not found in $pdf" >&2
    exit 1
  }
fi

echo "OK: $pdf contains expected text and no TeX/token errors."
