#!/usr/bin/env bash
# install-hooks.sh — Install Hermes gateway hooks from pub-resource repo
#
# Usage:
#   ./install-hooks.sh                          # install all hooks to ~/.hermes/hooks/
#   ./install-hooks.sh online-notify            # install specific hook
#   ./install-hooks.sh -d /custom/path          # install all to custom path
#   ./install-hooks.sh -d /custom/path online-notify  # specific hook to custom path
#   ./install-hooks.sh -l                       # list available hooks
#   ./install-hooks.sh --dry-run                # show what would be installed
#
set -euo pipefail

REPO_URL="git@github.com:bonaluo/pub-resource.git"
REPO_DIR="pub-resource"
HOOKS_SUBDIR="hermes/hooks"
DEFAULT_INSTALL_DIR="$HOME/.hermes/hooks"
TEMP_BASE="/tmp/pub-resource-hooks-$$"

INSTALL_DIR=""
HOOK_NAME=""
LIST_ONLY=false
DRY_RUN=false
CLONE_DIR=""

usage() {
    cat <<'EOF'
install-hooks.sh — Install Hermes gateway hooks from pub-resource repo

Usage:
  install-hooks.sh [OPTIONS] [HOOK_NAME]

Options:
  -d, --dir DIR     Install directory (default: ~/.hermes/hooks)
  -l, --list        List available hooks and exit
  --dry-run         Show what would be installed without copying
  -h, --help        Show this help message

Arguments:
  HOOK_NAME         Specific hook to install (default: all hooks)

Examples:
  install-hooks.sh                          # install all hooks to ~/.hermes/hooks
  install-hooks.sh online-notify            # install only online-notify
  install-hooks.sh -d ~/my-hooks            # install all to custom dir
  install-hooks.sh -l                       # list available hooks
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -d|--dir)
                INSTALL_DIR="$2"
                shift 2
                ;;
            -l|--list)
                LIST_ONLY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                if [[ -z "$HOOK_NAME" ]]; then
                    HOOK_NAME="$1"
                else
                    echo "Error: unexpected argument '$1'" >&2
                    usage >&2
                    exit 1
                fi
                shift
                ;;
        esac
    done
    if [[ -z "$INSTALL_DIR" ]]; then
        INSTALL_DIR="$DEFAULT_INSTALL_DIR"
    fi
}

clone_repo() {
    CLONE_DIR="$TEMP_BASE"
    rm -rf "$CLONE_DIR"
    git clone --depth 1 "$REPO_URL" "$CLONE_DIR" 2>&1 | sed 's/^/  /'
}

list_hooks() {
    local hooks_dir="$1/$HOOKS_SUBDIR"
    if [[ ! -d "$hooks_dir" ]]; then
        echo "No hooks found in repository."
        return
    fi
    echo "Available hooks:"
    for d in "$hooks_dir"/*/; do
        [[ -d "$d" ]] || continue
        local name
        name=$(basename "$d")
        local desc=""
        if [[ -f "$d/HOOK.yaml" ]]; then
            desc=$(grep -m1 '^description:' "$d/HOOK.yaml" 2>/dev/null | sed 's/^description: *//')
        fi
        printf "  %-20s %s\n" "$name" "$desc"
    done
}

install_hook() {
    local src="$1"
    local name
    name=$(basename "$src")
    local dest="$INSTALL_DIR/$name"

    echo "Installing: $name → $dest"

    if $DRY_RUN; then
        echo "  (dry-run, skipping actual copy)"
        return 0
    fi

    mkdir -p "$dest"
    cp -r "$src"/* "$dest/"
    echo "  ✓ Done"
}

main() {
    parse_args "$@"

    echo "Cloning pub-resource repo..."
    clone_repo

    local hooks_dir="$CLONE_DIR/$HOOKS_SUBDIR"

    if [[ ! -d "$hooks_dir" ]]; then
        echo "Error: hermes/hooks directory not found in repository." >&2
        rm -rf "$CLONE_DIR"
        exit 1
    fi

    if $LIST_ONLY; then
        list_hooks "$CLONE_DIR"
        rm -rf "$CLONE_DIR"
        exit 0
    fi

    echo "Install directory: $INSTALL_DIR"
    echo ""

    if [[ -n "$HOOK_NAME" ]]; then
        # Install specific hook
        local src="$hooks_dir/$HOOK_NAME"
        if [[ ! -d "$src" ]]; then
            echo "Error: hook '$HOOK_NAME' not found in repository." >&2
            echo ""
            list_hooks "$CLONE_DIR"
            rm -rf "$CLONE_DIR"
            exit 1
        fi
        install_hook "$src"
    else
        # Install all hooks
        local count=0
        for d in "$hooks_dir"/*/; do
            [[ -d "$d" ]] || continue
            install_hook "$d"
            ((count++))
        done
        if [[ $count -eq 0 ]]; then
            echo "No hooks found to install."
        else
            echo ""
            echo "Installed $count hook(s) to $INSTALL_DIR"
        fi
    fi

    rm -rf "$CLONE_DIR"
    echo "Cleanup complete."
}

main "$@"
