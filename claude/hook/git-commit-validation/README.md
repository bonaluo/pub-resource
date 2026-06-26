# Git Commit Validation Hook

Claude Code `PreToolUse` hook that intercepts `git commit -m` and validates commit messages against the [Conventional Commits](https://www.conventionalcommits.org/) format.

## Quick Install

### 1. Add the hook script

Copy `commit-check.sh` to your project's `.claude/hooks/` directory:

```bash
cp commit-check.sh /path/to/your-project/.claude/hooks/
chmod +x /path/to/your-project/.claude/hooks/commit-check.sh
```

### 2. Register in settings.json

In your project's `.claude/settings.json` (project-shared) or `~/.claude/settings.json` (global):

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/commit-check.sh"
      }]
    }]
  }
}
```

To restrict to only git commit commands, use a narrower matcher:

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash(git commit *)",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/commit-check.sh"
      }]
    }]
  }
}
```

## Format Rules

| Rule | Description |
|------|-------------|
| **Line 1** | `<type>: <description>` — type must be one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert` |
| **Line 2** | Must be blank (separates subject from body) |
| **Body lines** | Each line must start with `- ` (dash + space) |

### Valid Example

```
feat: 添加用户登录功能

- 实现用户名密码认证
- 添加 Token 刷新机制
- 集成现有用户表结构
```

### Invalid Examples

```
repaired copy functionality       ← missing type: prefix
fix: add fallback                 ← second line not blank
 - extra space before dash        ← missing dash prefix
```

## How It Works

### Hook Event: `PreToolUse`

Fires **before** every Bash tool execution. The hook:

1. Reads `$CLAUDE_TOOL_INPUT` env var (JSON with the full tool input)
2. Extracts `.command` via `jq`
3. If the command is `git commit -m "..."`, extracts and validates the message
4. Non-commit commands pass through immediately (exit 0)

### Exit Code Convention

| Exit Code | Meaning |
|-----------|---------|
| `0` | Allow the command |
| `2` | Block the command — stdout is shown to the model as error reason |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_TOOL_INPUT` | JSON of the Bash tool input, e.g. `{"command": "git commit -m \"...\"", "workdir": "..."}` |

## Dependencies

- `jq` — JSON processor (apt: `sudo apt install jq`, brew: `brew install jq`)

## Prior Art

This hook was originally written as a `before_command` hook for Hermes Agent, then migrated to Claude Code's `PreToolUse` event when the hook API changed. The migration diff illustrates the key differences:

| Aspect | Old (Hermes) | New (Claude Code) |
|--------|-------------|-------------------|
| Event name | `before_command` (invalid) | `PreToolUse` |
| Config format | `"before_command": "script"` | `"PreToolUse": [{"matcher": "Bash", "hooks": [...]}]` |
| Input | `$1` (raw command string) | `$CLAUDE_TOOL_INPUT` (JSON env var) |
| Block signal | `exit 1` | `exit 2` |
| Error display | stderr | stdout |

## See Also

- [Claude Code Hooks Documentation](https://code.claude.com/docs/en/hooks) — official reference for all 8 hook types
- [Conventional Commits](https://www.conventionalcommits.org/) — the commit message specification
