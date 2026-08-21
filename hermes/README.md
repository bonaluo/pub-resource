# Hermes Resources

This directory contains reusable Hermes Agent resources hosted in the pub-resource repo.

## Hooks

Gateway event hooks for Hermes Agent. Each hook is a directory containing `HOOK.yaml` (event subscription) and `handler.py` (handler logic).

### Available Hooks

| Hook | Description |
|------|-------------|
| `online-notify` | Send "Hermes已上线" notification to all messaging channels on gateway startup |

### Installation

Use the install script to pull and install hooks:

```bash
# Install all hooks to ~/.hermes/hooks/
./hermes/install-hooks.sh

# Install a specific hook
./hermes/install-hooks.sh online-notify

# Install to a custom directory
./hermes/install-hooks.sh -d /custom/path

# List available hooks
./hermes/install-hooks.sh -l

# Dry run (show what would be installed)
./hermes/install-hooks.sh --dry-run
```

You can also run it directly from GitHub without cloning:

```bash
bash <(curl -s https://raw.githubusercontent.com/bonaluo/pub-resource/main/hermes/install-hooks.sh) -- -l
```

### Manual Installation

```bash
cp -r hermes/hooks/<hook-name> ~/.hermes/hooks/
```
