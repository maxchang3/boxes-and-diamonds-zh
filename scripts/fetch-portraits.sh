#!/bin/sh
# Fetch the B&D cover portraits from the official source repository
# (OpenLogicProject/portraits, linked from bd.openlogicproject.org).
# Usage: ./scripts/fetch-portraits.sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p assets/portraits
BASE="https://raw.githubusercontent.com/OpenLogicProject/portraits/master"
for name in antonelli barcan carnap heyting kripke lewis prior; do
  out="assets/portraits/${name}-circle.pdf"
  if [ -s "$out" ]; then
    echo "OK ${name}-circle.pdf (cached)"
    continue
  fi
  tmp="${out}.tmp.$$"
  trap 'rm -f "$tmp"' EXIT HUP INT TERM
  curl -fsSL "${BASE}/${name}-circle.pdf" -o "$tmp"
  mv "$tmp" "$out"
  trap - EXIT HUP INT TERM
  echo "OK ${name}-circle.pdf ($(wc -c < "$out") bytes)"
done
echo "All portraits fetched into assets/portraits/."
