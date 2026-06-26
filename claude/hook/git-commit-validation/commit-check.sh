#!/usr/bin/env bash
set -e

# PreToolUse hook: intercept Bash(git commit -m) and validate commit messages.
# Uses $CLAUDE_TOOL_INPUT env var (JSON of the Bash tool input).
# exit 0 = allow, exit 2 = block (stdout is shown to the model as error reason).

if [ -z "${CLAUDE_TOOL_INPUT:-}" ]; then
    exit 0
fi

CMD=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '.command // empty')

if [ -z "$CMD" ] || ! echo "$CMD" | grep -qE '^git commit'; then
    exit 0
fi

if ! echo "$CMD" | grep -qE '\-m'; then
    exit 0
fi

MSG=$(echo "$CLAUDE_TOOL_INPUT" | jq -r '
    .command
    | capture("-m\\s*\"(?<msg>(?:[^\"\\\\]|\\\\.)*)\"")
    | .msg
    | gsub("\\\\n"; "\n") | gsub("\\\\t"; "\t") | gsub("\\\\\""; "\"")
')

if [ -z "$MSG" ]; then
    MSG=$(echo "$CMD" | sed -n 's/.*\-m\s*"\([^"\]*\(\\.[^"\]*\)*\)".*/\1/p')
fi

if [ -z "$MSG" ]; then
    exit 0
fi

# Split commit message by lines
LINE1=$(echo "$MSG" | sed -n '1p')
LINE2=$(echo "$MSG" | sed -n '2p')

ERRORS=""

# 检查第一行: type: 描述
if ! echo "$LINE1" | grep -qE '^(feat|fix|docs|style|refactor|perf|test|chore|ci|build|revert):(.+)$'; then
    ERRORS="${ERRORS}❌ 第一行格式错误。应为: <type>: <描述>\n   有效 type: feat, fix, docs, style, refactor, perf, test, chore, ci, build, revert\n   示例: fix: 修复复制功能兼容性问题\n"
fi

# 检查第二行: 空行
if [ -n "$LINE2" ]; then
    ERRORS="${ERRORS}❌ 第二行必须是空行（分隔标题和正文）\n"
fi

# 检查第三行起: 以 "- " 开头（如果正文非空）
REST=$(echo "$MSG" | tail -n +3)
if [ -n "$REST" ]; then
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        if ! echo "$line" | grep -qE '^- '; then
            ERRORS="${ERRORS}❌ 正文行必须以 \"- \" 开头: $line\n   示例: - 添加兼容性降级方案\n"
            break
        fi
    done <<< "$REST"
fi

if [ -n "$ERRORS" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  🚫 Git 提交信息格式不符合规范"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo -e "$ERRORS"
    echo "───────────────────────────────────────────────────────────────"
    echo "  💡 完整的提交规范请参考 /git-conventions skill"
    echo "───────────────────────────────────────────────────────────────"
    echo "  正确格式示例："
    echo ""
    echo '  feat: 添加用户登录功能'
    echo ''
    echo '  - 实现用户名密码认证'
    echo '  - 添加 Token 刷新机制'
    echo '  - 集成现有用户表结构'
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    exit 2
fi

exit 0
