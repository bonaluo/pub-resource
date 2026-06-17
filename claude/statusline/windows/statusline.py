#!/usr/bin/env python3
"""Claude Code 状态栏脚本：显示目录、模型、上下文、Git、会话时长、时间"""

import json
import sys
import os
import subprocess
import time
from datetime import datetime, timezone

# 会话时间戳文件目录
_SESSION_DIR = os.path.expanduser("~/.claude/.sessions")
os.makedirs(_SESSION_DIR, exist_ok=True)


def _save_debug_json(data: dict) -> None:
    """保存运行时输入 JSON 到文件用于调试."""
    try:
        debug_file = os.path.expanduser("~/.claude/statusline_last_input.json")
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception:
        pass


def _get_ccswitch_model() -> str:
    """从 cc-switch 数据库读取当前实际使用的模型名称."""
    db_path = os.path.expanduser("~/.cc-switch/cc-switch.db")
    if not os.path.exists(db_path):
        return ""
    try:
        import sqlite3
        with sqlite3.connect(db_path, timeout=1.0) as conn:
            cur = conn.cursor()
            # 获取当前正在使用的 provider (is_current=1)
            cur.execute(
                "SELECT settings_config FROM providers WHERE is_current = 1 AND app_type = 'claude' LIMIT 1"
            )
            row = cur.fetchone()
            if row and row[0]:
                import json
                settings = json.loads(row[0])
                # 从 env 中获取模型名称
                env = settings.get("env", {})
                model = env.get("ANTHROPIC_MODEL", "")
                # 如果有 SONNET/OPUS 后缀的模型名，取具体名称
                sonnet = env.get("ANTHROPIC_DEFAULT_SONNET_MODEL_NAME", "")
                opus = env.get("ANTHROPIC_DEFAULT_OPUS_MODEL_NAME", "")
                haiku = env.get("ANTHROPIC_DEFAULT_HAIKU_MODEL_NAME", "")
                # 返回最具体的模型名
                if sonnet and sonnet != model and model:
                    return f"{model} → {sonnet}"
                if model:
                    return model
                if sonnet:
                    return sonnet
                if opus:
                    return opus
                if haiku:
                    return haiku
            return ""
    except Exception:
        # 如果数据库无法访问，返回空字符串让主逻辑 fallback
        return ""


def _get_effort_from_settings() -> str:
    """从 settings.json 读取 effortLevel."""
    try:
        with open(os.path.expanduser("~/.claude/settings.json"), "r", encoding="utf-8") as f:
            settings = json.load(f)
        effort = settings.get("effortLevel", "")
        if effort:
            return effort
    except Exception:
        pass
    return os.environ.get("CLAUDE_CODE_EFFORT_LEVEL", "")


def _session_file(session_id: str) -> str:
    """获取指定会话的时间戳文件路径."""
    safe_id = session_id.replace("/", "_").replace("\\", "_")
    return os.path.join(_SESSION_DIR, f"{safe_id}.json")


def _load_session_state(session_id: str) -> dict:
    """读取会话状态：start_time, last_activity."""
    path = _session_file(session_id)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_session_state(session_id: str, state: dict) -> None:
    """保存会话状态."""
    try:
        with open(_session_file(session_id), "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def get_git_info(cwd: str) -> dict:
    """获取当前 Git 分支名和是否有未提交更改."""
    try:
        branch = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True, timeout=2
        )
        branch_name = branch.stdout.strip()

        if not branch_name:
            return {"branch": "", "dirty": False, "staged": 0, "unstaged": 0, "untracked": 0}

        status = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain"],
            capture_output=True, text=True, timeout=2
        )
        lines = [l for l in status.stdout.strip().split("\n") if l]

        staged = 0
        unstaged = 0
        untracked = 0

        for line in lines:
            if len(line) < 2:
                continue
            idx = line[0]
            wt = line[1]

            if idx == "?" and wt == "?":
                untracked += 1
                continue

            if idx != " ":
                staged += 1
            if wt != " ":
                unstaged += 1

        return {
            "branch": branch_name,
            "dirty": bool(staged or unstaged or untracked),
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
        }
    except Exception:
        return {"branch": "", "dirty": False, "staged": 0, "unstaged": 0, "untracked": 0}


def format_duration(seconds: int) -> str:
    """将秒数格式化为友好的持续时间字符串."""
    if seconds < 60:
        return f"{seconds}秒"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}分钟"
    hours = minutes // 60
    if hours < 24:
        remainder_m = minutes % 60
        return f"{hours}小时{remainder_m}分" if remainder_m else f"{hours}小时"
    days = hours // 24
    remainder_h = hours % 24
    return f"{days}天{remainder_h}小时" if remainder_h else f"{days}天"


def build_bar(percentage: int, width: int = 10) -> str:
    """基于方块字符构建进度条."""
    filled = int(percentage * width / 100)
    return "█" * filled + "░" * (width - filled)


def get_context_color(percentage: int) -> str:
    """返回上下文使用率的 ANSI 颜色码."""
    if percentage >= 90:
        return "\033[31m"
    elif percentage >= 70:
        return "\033[33m"
    return "\033[32m"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, Exception):
        print("--")
        return

    # 保存调试数据
    _save_debug_json(data)

    session_id = data.get("session_id", "unknown")

    # 获取模型信息：Claude 传入的模型 + ccswitch 实际路由的模型
    claude_model = data.get("model", {}).get("display_name", "?")
    ccswitch_model = _get_ccswitch_model()
    # 构建模型显示字符串：ccswitch实际模型 → Claude模型
    if ccswitch_model and ccswitch_model != claude_model:
        model = f"{claude_model} → {ccswitch_model}"
    else:
        model = claude_model

    cwd = data.get("workspace", {}).get("current_dir", os.getcwd())
    pct = int(float(data.get("context_window", {}).get("used_percentage", 0)))

    # effort 级别：多重来源 fallback
    effort = ""
    if "effort" in data and isinstance(data.get("effort"), dict):
        effort = data["effort"].get("level", "")
    if not effort:
        effort = os.environ.get("CLAUDE_CODE_EFFORT_LEVEL", "")
    if not effort:
        effort = _get_effort_from_settings()
    if not effort:
        effort = "max"  # 默认值

    # ANSI 颜色
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    # --- Effort 级别 ---
    effort_map = {"low": "低", "medium": "中", "high": "高", "xhigh": "超高", "max": "最高"}
    effort_str = effort_map.get(effort, effort) if effort else ""

    # --- 会话时长 ---
    now = time.time()
    state = _load_session_state(session_id)
    if "start_time" not in state:
        state["start_time"] = now
    start_time = state.get("start_time", now)
    duration_seconds = int(now - start_time)
    duration_str = format_duration(duration_seconds)

    # --- 上次活动时间 ---
    last_activity_time = state.get("last_activity", now)
    idle_seconds = int(now - last_activity_time)
    state["last_activity"] = now
    _save_session_state(session_id, state)

    if idle_seconds < 60:
        last_activity_str = "刚刚"
    else:
        last_activity_str = format_duration(idle_seconds)

    # --- Git 状态 ---
    git = get_git_info(cwd)
    git_part = ""
    if git["branch"]:
        bits = []
        if git["staged"]:
            bits.append(f"+{git['staged']}")
        if git["unstaged"]:
            bits.append(f"~{git['unstaged']}")
        if git["untracked"]:
            bits.append(f"?{git['untracked']}")
        dirty_marker = " ".join(bits) if bits else ""
        if dirty_marker:
            dirty_marker = f" \033[33m{dirty_marker}\033[0m"
        git_part = f"🌿 {git['branch']}{dirty_marker}"

    # --- 当前时间 ---
    time_str = datetime.now().strftime("%H:%M")

    # --- 上下文进度条 ---
    ctx_color = get_context_color(pct)
    bar = build_bar(pct)
    ctx_part = f"{ctx_color}{bar} {pct}%{RESET}"

    # --- 最终输出 ---
    session_info = f"⏱️ {duration_str} (上次: {last_activity_str})"
    parts = [f"{BOLD}📂 {cwd}{RESET}"]
    parts.append(f"🤖 {CYAN}{model}{RESET}")
    if effort_str:
        parts.append(f"{MAGENTA}⚡ {effort_str}{RESET}")
    if git_part:
        parts.append(git_part)
    parts.append(f"{ctx_color}{ctx_part}{RESET}")
    parts.append(session_info)
    parts.append(f"🕐 {time_str}")
    print(" | ".join(parts))


if __name__ == "__main__":
    main()