#!/usr/bin/env python3
"""Token and time statistics of the Claude Code sessions that built this project.

Reads Claude Code's local session logs (~/.claude/projects/<project>/*.jsonl, including the planning sessions
from the project's former folder name) and reports tokens and time: in total, and up to each milestone
(a git tag such as m1-grid, or any commit given with --until).

Usage: python3 tools/stats.py [--until <git-ref>] [--project-dirs dir1,dir2]
"""
import argparse, glob, json, os, subprocess
from datetime import datetime, timezone

ACTIVE_GAP_S = 10 * 60   # gaps longer than this between log entries do not count as working time


def project_dirs():
    root = os.path.expanduser("~/.claude/projects")
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    slug = here.replace("/", "-")
    dirs = [os.path.join(root, slug)]
    old = os.path.join(root, slug.replace("project-second-credit", "renovated-games"))
    if os.path.isdir(old):
        dirs.insert(0, old)
    return [d for d in dirs if os.path.isdir(d)]


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load(dirs):
    """One record per API response: (time, input, cache_write, cache_read, output, model)."""
    seen = {}
    times = []
    for d in dirs:
        for path in glob.glob(os.path.join(d, "**", "*.jsonl"), recursive=True):
            with open(path, errors="replace") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if "timestamp" in e:
                        times.append(ts(e["timestamp"]))
                    msg = e.get("message")
                    if not isinstance(msg, dict) or "usage" not in msg:
                        continue
                    key = (msg.get("id"), e.get("requestId"))
                    u = msg["usage"]
                    seen[key] = (ts(e["timestamp"]), u.get("input_tokens", 0),
                                 u.get("cache_creation_input_tokens", 0), u.get("cache_read_input_tokens", 0),
                                 u.get("output_tokens", 0), msg.get("model", "?"))
    return sorted(seen.values()), sorted(times)


def summary(records, times, until=None):
    rs = [r for r in records if until is None or r[0] <= until]
    ts_ = [t for t in times if until is None or t <= until]
    if not ts_:
        return None
    active = sum(min((b - a).total_seconds(), ACTIVE_GAP_S) for a, b in zip(ts_, ts_[1:])
                 if (b - a).total_seconds() <= ACTIVE_GAP_S)
    return {
        "requests": len(rs),
        "input": sum(r[1] for r in rs), "cache_write": sum(r[2] for r in rs),
        "cache_read": sum(r[3] for r in rs), "output": sum(r[4] for r in rs),
        "start": ts_[0], "end": ts_[-1], "active_h": active / 3600,
    }


def git_time(ref):
    out = subprocess.run(["git", "log", "-1", "--format=%cI", ref], capture_output=True, text=True, check=True)
    return datetime.fromisoformat(out.stdout.strip()).astimezone(timezone.utc)


def show(label, s):
    total_in = s["input"] + s["cache_write"] + s["cache_read"]
    print(f"{label}")
    print(f"  requests       {s['requests']:>14,}")
    print(f"  output tokens  {s['output']:>14,}")
    print(f"  input tokens   {total_in:>14,}  (new {s['input']:,}, cache write {s['cache_write']:,}, cache read {s['cache_read']:,})")
    print(f"  all tokens     {total_in + s['output']:>14,}")
    print(f"  wall clock     {s['start']:%Y-%m-%d %H:%M} -> {s['end']:%Y-%m-%d %H:%M} UTC "
          f"({(s['end'] - s['start']).total_seconds() / 3600:.1f} h)")
    print(f"  active time    {s['active_h']:>13.1f} h  (gaps over {ACTIVE_GAP_S // 60} min not counted)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--until", action="append", default=[], help="git ref (tag or commit); repeatable")
    ap.add_argument("--project-dirs", help="comma-separated Claude Code project log folders")
    a = ap.parse_args()
    dirs = a.project_dirs.split(",") if a.project_dirs else project_dirs()
    records, times = load(dirs)
    tags = a.until or [t for t in subprocess.run(["git", "tag", "--sort=creatordate"], capture_output=True,
                                                  text=True).stdout.split() if t.startswith("m")]
    for ref in tags:
        s = summary(records, times, git_time(ref))
        if s:
            show(f"Up to {ref}:", s)
    show("All sessions so far:", summary(records, times))


if __name__ == "__main__":
    main()
