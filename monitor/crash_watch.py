"""
crash_watch.py — polls FastAPI's /health endpoint. The moment it stops
responding, it captures a snapshot of the FastAPI logs + docker compose ps
output to logs/crash_<timestamp>.txt.

Usage:
    python monitor/crash_watch.py &
    python run_test.py flash_event
"""

import argparse
import datetime
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_HEALTH_URL = "http://127.0.0.1:8000/health"
DEFAULT_POLL_SECONDS = 3
DEFAULT_SERVER_LOG = Path("logs/fastapi/server.log")
DEFAULT_CRASH_DIR = Path("logs")


def check_health(url, timeout=3.0):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            if resp.status == 200:
                return True, "ok"
            return False, f"unexpected status {resp.status}"
    except urllib.error.URLError as e:
        return False, f"connection error: {e.reason}"
    except Exception as e:
        return False, f"unexpected error: {e}"


def tail_file(path, n_lines=200):
    if not path.exists():
        return f"(no log file found at {path})"
    try:
        lines = path.read_text(errors="replace").splitlines()
        return "\n".join(lines[-n_lines:])
    except Exception as e:
        return f"(failed to read {path}: {e})"


def docker_compose_ps():
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", "infra/docker-compose.yml", "ps"],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"(could not run docker compose ps: {e})"


def write_crash_snapshot(crash_dir, server_log, reason):
    crash_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = crash_dir / f"crash_{timestamp}.txt"

    content = [
        f"=== Crash snapshot — {datetime.datetime.now().isoformat()} ===",
        f"Reason: {reason}",
        "",
        "--- docker compose ps ---",
        docker_compose_ps(),
        "",
        f"--- last 200 lines of {server_log} ---",
        tail_file(server_log),
    ]
    snapshot_path.write_text("\n".join(content))
    return snapshot_path


def main():
    parser = argparse.ArgumentParser(description="Crash watchdog for the FastAPI server")
    parser.add_argument("--url", default=DEFAULT_HEALTH_URL)
    parser.add_argument("--interval", type=float, default=DEFAULT_POLL_SECONDS)
    parser.add_argument("--server-log", type=Path, default=DEFAULT_SERVER_LOG)
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_CRASH_DIR)
    parser.add_argument("--fail-threshold", type=int, default=2)
    args = parser.parse_args()

    print(f"[crash_watch] watching {args.url} every {args.interval}s (snapshot dir: {args.logs_dir})")

    consecutive_failures = 0
    last_reason = ""

    try:
        while True:
            healthy, reason = check_health(args.url)
            if healthy:
                if consecutive_failures > 0:
                    print(f"[crash_watch] recovered after {consecutive_failures} failed check(s)")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                last_reason = reason
                print(f"[crash_watch] health check failed ({consecutive_failures}/{args.fail_threshold}): {reason}")

                if consecutive_failures == args.fail_threshold:
                    snapshot_path = write_crash_snapshot(args.logs_dir, args.server_log, last_reason)
                    print(f"[crash_watch] CRASH DETECTED — snapshot written to {snapshot_path}")
                    consecutive_failures = args.fail_threshold + 1

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n[crash_watch] stopped")
        sys.exit(0)


if __name__ == "__main__":
    main()
