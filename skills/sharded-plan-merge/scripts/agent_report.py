"""Extract a subagent's final report from its Claude Code transcript and check completeness.

Usage:
  python agent_report.py <agent-name> [--expect "H1,H2,..."] [--sentinel "<!-- END -->"]
                         [--out DIR] [--projects DIR] [--max-bytes N]

- Finds ~/.claude/projects/**/subagents/agent-*<name>-*.jsonl (a named agent's file is
  agent-a<name>-<hash>.jsonl); the newest match wins.
- Takes the LAST assistant text block (never the longest: a later SendMessage reply is
  shorter than the first report, and the last block is the agent's current answer).
- Exit 1 if any --expect heading or the --sentinel (when given) is missing.
- With --out: writes report.md plus one file per '## ' section, each under --max-bytes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def last_text(path: Path) -> str:
    last = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") == "api-request-blob":
            continue
        msg = rec.get("message") or {}
        if msg.get("role") != "assistant" or not isinstance(msg.get("content"), list):
            continue
        for block in msg["content"]:
            if block.get("type") == "text" and block.get("text", "").strip():
                last = block["text"]
    return last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--expect", default="")
    ap.add_argument("--sentinel", default="")
    ap.add_argument("--out")
    ap.add_argument("--projects", default=str(Path.home() / ".claude" / "projects"))
    ap.add_argument("--max-bytes", type=int, default=24000)
    a = ap.parse_args()

    matches = sorted(Path(a.projects).glob(f"**/subagents/agent-*{a.name}-*.jsonl"),
                     key=lambda p: p.stat().st_mtime)
    if not matches:
        print(f"no transcript matches agent-*{a.name}-*.jsonl under {a.projects}", file=sys.stderr)
        return 2
    report = last_text(matches[-1])
    if not report:
        print(f"{matches[-1].name}: no assistant text yet (agent still running?)", file=sys.stderr)
        return 2

    missing = [h for h in (x.strip() for x in a.expect.split(",")) if h and h not in report]
    if a.sentinel and a.sentinel not in report:
        missing.append(f"sentinel {a.sentinel!r}")

    if a.out:
        out = Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(report, encoding="utf-8")
        for i, part in enumerate(re.split(r"(?m)^(?=## )", report)):
            data = part.encode("utf-8")
            for j in range(0, max(len(data), 1), a.max_bytes):
                chunk = data[j:j + a.max_bytes].decode("utf-8", errors="ignore")
                (out / f"section-{i:02d}-{j // a.max_bytes}.md").write_text(chunk, encoding="utf-8")

    print(f"{matches[-1].name}: {len(report)} chars; missing: {missing or 'none'}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
