#!/bin/sh
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT
#
# Export the public release of Wheelly from the working repository.
#
# WHY A SCRIPT: the working repository keeps
# the whole history, the working notes and the record of the test machine; the
# public one gets only what is needed to build the wheel - print, wire, flash,
# install the driver, regenerate the CAD. What stays private is listed below,
# once, instead of being remembered by whoever publishes; and the scan at the end
# refuses to go on if a password, an address, a serial number or a private
# document slipped through.
#
#     tools/publish.sh DEST            export HEAD into DEST (must not exist)
#
# It exports tracked files only (git archive), so out/, promo/, .venv/ and
# .claude/ never travel. It does not commit, push or touch GitHub.
set -eu

DEST="${1:?usage: tools/publish.sh DEST (a folder that does not exist yet)}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -e "$DEST" ] && { echo "$DEST exists: choose a new folder" >&2; exit 1; }

# What stays private, and why
PRIVATE="
ASTROARCH.md
CLAUDE.md
DA_FARE.md
mechanics/wheelly-cad/DA_FARE.md
mechanics/wheelly-cad/VALUTAZIONE_ELETTRONICA_ZONA_MOTORE.md
mechanics/wheelly-cad/src/special_panel_asbuilt.py
mechanics/wheelly-cad/src/check_thin.py
mechanics/wheelly-cad/src/promo
tools/publish_private_patterns.txt
pcb/schemi/Disposizione componenti.af
"
#   ASTROARCH.md        the log of the private test machine (host, credentials)
#   tools/publish_private_patterns.txt  the private strings the scan looks for:
#                       they are secrets themselves, so they stay out
#   CLAUDE.md, DA_FARE  working notes, in Italian, day by day; ROADMAP.md is
#                       their public summary
#   VALUTAZIONE_...     a closed study, in Italian
#   special_panel_...   a one-off part for the prototype as it was built
#   check_thin.py       a check the build does not run
#   src/promo           the launch video's scenes
#   *.af                the hand-drawn layout the generated one replaced
# plus, by pattern below: the one-off studies (src/study_*.py, src/sketch_*.py;
# src/study_paths/ stays - it regenerates the assembly paths the checks use)
# and the makers' models in mechanics/others/ (not redistributable:
# mechanics/others/README.md says where to download them).

mkdir -p "$DEST"
git -C "$ROOT" archive HEAD | tar -x -C "$DEST"
cd "$DEST"
echo "$PRIVATE" | while IFS= read -r p; do
    if [ -n "$p" ]; then rm -rf "./$p"; fi
done
rm -f mechanics/wheelly-cad/src/study_*.py mechanics/wheelly-cad/src/sketch_*.py
find mechanics/others -type f ! -name README.md -delete

# The scan. Every pattern is something that must never be public; a hit stops
# the publication. The generic ones are here (this script is excluded from its
# own scan); the private ones come from a file that is not exported.
BAD=0
scan() {
    hits=$(grep -rIl -E "$1" . 2>/dev/null | grep -v '^./tools/publish.sh$' || true)
    if [ -n "$hits" ]; then
        echo "BLOCKED - $2:"; echo "$hits" | sed 's/^/    /'
        BAD=1
    fi
}
scan "192\.168\.[0-9]" "a LAN address"
# The private patterns (serial, MAC, token, local paths) are read from a file
# that is itself left out of the export: written here, even split in pieces,
# they would publish what they protect. No file, no publication.
PATTERNS="$ROOT/tools/publish_private_patterns.txt"
[ -f "$PATTERNS" ] || { echo "BLOCKED - $PATTERNS is missing: the scan would be blind" >&2; exit 2; }
while IFS="$(printf '\t')" read -r pat why; do
    case "$pat" in ''|'#'*) continue ;; esac
    scan "$pat" "$why"
done < "$PATTERNS"
scan "DA_""FARE|ASTRO""ARCH\.md|CLAUDE""\.md" "a reference to a private document"
if [ "$BAD" -ne 0 ]; then
    echo "The export in $DEST is NOT publishable: fix the source, commit, run again."
    exit 2
fi
N=$(find . -type f | wc -l | tr -d ' ')
echo "exported $N files into $DEST - scan clean"
