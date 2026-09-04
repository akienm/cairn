#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 4 ]; then
    echo "usage: ask_user.sh <question> <type> <on-yes> <on-no>" >&2
    exit 1
fi

QUESTION="$1"
TYPE="$2"
ON_YES="$3"
ON_NO="$4"

case "$TYPE" in
    YN)
        printf '%s [Y/N] ' "$QUESTION" >&2
        read -r ANSWER
        case "$ANSWER" in
            [Yy]|[Yy][Ee][Ss])
                exec bash -c "$ON_YES"
                ;;
            [Nn]|[Nn][Oo])
                exec bash -c "$ON_NO"
                ;;
            *)
                echo "error: expected Y or N, got '$ANSWER'" >&2
                exit 1
                ;;
        esac
        ;;
    *)
        echo "error: unknown type '$TYPE' (known: YN)" >&2
        exit 1
        ;;
esac
