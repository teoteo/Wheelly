#!/bin/sh
# SPDX-FileCopyrightText: 2026 Matteo Beretta
# SPDX-License-Identifier: MIT

# Open the air-gap test bench in the browser.
#
#     ./gap_page.sh        serves the page on localhost and opens it in Chrome
#
# Served from localhost and not as file:// because Web Serial wants a secure
# context. Chrome (or Edge): Safari and Firefox have no Web Serial. The IDE's
# serial monitor and the one of flash.sh must be closed: only one program at a
# time can hold the port.
set -e
cd "$(dirname "$0")/gap_page"
PORT=${1:-8770}
open -a "Google Chrome" "http://localhost:$PORT/" 2>/dev/null || open "http://localhost:$PORT/"
echo "page on http://localhost:$PORT/  - ctrl-C to close"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
