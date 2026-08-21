"""Send an online notification to all configured messaging channels on gateway startup."""

import json
import logging
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("hooks.online-notify")

LOG_FILE = Path.home() / ".hermes" / "hooks" / "online-notify" / "notify.log"

# Seconds to wait after gateway:startup before sending — gives platform
# adapters time to finish connecting (especially QQ, WebSocket-based).
STARTUP_DELAY = 15

# Max send retries per platform.
MAX_RETRIES = 3
RETRY_INTERVAL = 5


def _discover_targets() -> list[str]:
    """Use `hermes send --list --json` to discover all available targets.

    Returns a list of 'platform:chat_id' strings. Falls back to bare
    platform names if JSON parsing fails.
    """
    try:
        result = subprocess.run(
            ["hermes", "send", "--list", "--json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            logger.warning("online-notify: send --list failed: rc=%d", result.returncode)
            return []
        data = json.loads(result.stdout)
        targets = []
        for platform, channels in data.get("platforms", {}).items():
            for ch in channels:
                chat_id = ch.get("id", "")
                if chat_id:
                    targets.append(f"{platform}:{chat_id}")
        logger.info("online-notify: discovered targets: %s", targets)
        return targets
    except Exception as e:
        logger.warning("online-notify: target discovery error: %s", e)
        return []


def _send_to_target(target: str) -> bool:
    """Try to send the online notification to one target."""
    msg = f"✅ Hermes 已上线\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                ["hermes", "send", "-t", target, "-q", msg],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                logger.info("online-notify: sent to %s (attempt %d)", target, attempt)
                return True
            else:
                logger.warning(
                    "online-notify: send to %s failed (attempt %d/%d): rc=%d stderr=%s",
                    target, attempt, MAX_RETRIES, result.returncode,
                    result.stderr.strip()[:200],
                )
        except Exception as e:
            logger.warning(
                "online-notify: send to %s error (attempt %d/%d): %s",
                target, attempt, MAX_RETRIES, e,
            )
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_INTERVAL)
    return False


def _notify_all(platforms: list[str]) -> None:
    """Wait for platforms to connect, discover targets, then send notifications."""
    time.sleep(STARTUP_DELAY)

    # Discover actual send targets (platform:chat_id) instead of relying
    # on bare platform names which require a home channel to be set.
    targets = _discover_targets()
    if not targets:
        # Fallback: use bare platform names from the startup context
        targets = platforms
        logger.warning("online-notify: no targets discovered, falling back to bare platforms: %s", targets)

    results = {}
    for target in targets:
        results[target] = _send_to_target(target)

    # Log summary (keep last 100 entries to prevent unbounded growth)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "platforms": platforms,
        "targets": targets,
        "results": results,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Trim to last 100 lines
    try:
        lines = LOG_FILE.read_text().splitlines()
        if len(lines) > 100:
            LOG_FILE.write_text("\n".join(lines[-100:]) + "\n")
    except Exception:
        pass  # best-effort, never block notification

    succeeded = sum(1 for v in results.values() if v)
    logger.info(
        "online-notify: done — %d/%d targets notified", succeeded, len(targets),
    )


async def handle(event_type: str, context: dict) -> None:
    """Gateway hook entry point — fires on gateway:startup."""
    platforms = context.get("platforms", [])
    if not platforms:
        logger.warning("online-notify: no platforms in startup context, skipping")
        return

    logger.info("online-notify: gateway started with platforms: %s", platforms)

    # Run in a background thread so gateway startup isn't blocked.
    thread = threading.Thread(
        target=_notify_all,
        args=(platforms,),
        name="online-notify",
        daemon=True,
    )
    thread.start()
