#!/usr/bin/env bash
# Branch protection for main (US-01.2 / US-02.5), and the freeze at release (US-30.3).
#   scripts/protect-main.sh <owner/repo>            # PR + 1 owner review + required CI checks
#   scripts/protect-main.sh <owner/repo> --freeze   # same + lock the branch (read-only)
set -euo pipefail
REPO=${1:?usage: protect-main.sh <owner/repo> [--freeze]}
BODY=$(cat "$(dirname "$0")/../.github/protection.json")
if [[ ${2:-} == "--freeze" ]]; then BODY=$(echo "$BODY" | python3 -c 'import sys,json;d=json.load(sys.stdin);d["lock_branch"]=True;d["restrictions"]=None;print(json.dumps(d))'); fi
echo "$BODY" | gh api -X PUT "repos/$REPO/branches/main/protection" --input -
echo "protection applied to $REPO main ${2:-}"
