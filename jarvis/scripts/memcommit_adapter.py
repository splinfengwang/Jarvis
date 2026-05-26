#!/usr/bin/env python3
"""OpenViking memcommit adapter for Jarvis Runtime v0.3.

Direct HTTP API integration — no MCP/LLM intermediary required.
Tested: 2026-05-19, OpenViking v0.2.6 @ localhost:1933.

Usage from lifecycle scripts:
    from memcommit_adapter import commit_memory
    result = commit_memory(
        repo_root="/path/to/vault",
        kind="topic_update",
        topic="贾维斯运行时架构迭代",
        summary="Freeze topic: Phase A/B/C complete.",
        facts=["v0.3 acceptance-report updated", "42 fixtures pass"],
        decisions=["Keep AGENT.md as fallback"],
    )
    # result: {"status": "committed", "uri": "viking://...", "errors": []}
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from urllib import request
from urllib.error import URLError

DEFAULT_BASE_URL = "http://localhost:1933"
RESOURCES_ENDPOINT = "/api/v1/resources"
REQUEST_TIMEOUT = 30


def _build_frontmatter(
    kind: str = "topic_update",
    topic: str = "",
    summary: str = "",
) -> str:
    return (
        f"---\n"
        f"source: jarvis-runtime\n"
        f"kind: {kind}\n"
        f"topic: {topic}\n"
        f"summary: {summary}\n"
        f"created_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n"
        f"---\n"
    )


def _build_note_body(
    facts: list[str] | None = None,
    decisions: list[str] | None = None,
    preferences: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> str:
    parts: list[str] = []
    if facts:
        parts.append("## Facts\n\n" + "\n".join(f"- {f}" for f in facts))
    if decisions:
        parts.append("## Decisions\n\n" + "\n".join(f"- {d}" for d in decisions))
    if preferences:
        parts.append("## Preferences\n\n" + "\n".join(f"- {p}" for p in preferences))
    if next_actions:
        parts.append("## Next Actions\n\n" + "\n".join(f"- {a}" for a in next_actions))
    return "\n\n".join(parts) + "\n"


def build_payload(
    repo_root: str,
    kind: str = "topic_update",
    topic: str = "",
    summary: str = "",
    facts: list[str] | None = None,
    decisions: list[str] | None = None,
    preferences: list[str] | None = None,
    next_actions: list[str] | None = None,
) -> dict:
    """Build the AddResource request payload for OpenViking HTTP API."""
    date = time.strftime("%Y/%m/%d", time.gmtime())
    slug = topic.replace(" ", "-").replace("/", "-") or "memory"
    ts = time.strftime("%H%M%S", time.gmtime())
    dest_uri = f"viking://resources/kf580/{Path(repo_root).name}/.codex-memory/{date}/{ts}-{slug}.md"
    return {
        "to": dest_uri,
        "reason": f"jarvis-runtime: {kind}",
        "instruction": summary or f"Memory for topic: {topic}",
        "wait": True,
        "strict": False,
    }


def _write_temp_note(
    kind: str,
    topic: str,
    summary: str,
    facts: list[str] | None,
    decisions: list[str] | None,
    preferences: list[str] | None,
    next_actions: list[str] | None,
) -> str:
    """Write a temporary markdown note file for upload. Returns the temp path."""
    frontmatter = _build_frontmatter(kind, topic, summary)
    body = _build_note_body(facts, decisions, preferences, next_actions)
    content = frontmatter + "\n" + body
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", prefix="jarvis-memory-", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        return f.name


def commit_memory(
    repo_root: str,
    kind: str = "topic_update",
    topic: str = "",
    summary: str = "",
    facts: list[str] | None = None,
    decisions: list[str] | None = None,
    preferences: list[str] | None = None,
    next_actions: list[str] | None = None,
    base_url: str = DEFAULT_BASE_URL,
) -> dict:
    """Write a memory note to OpenViking via HTTP API.

    Returns:
        {"status": "committed", "uri": "viking://...", "detail": "..."}
        {"status": "skipped_or_failed", "uri": None, "detail": "reason"}
    """
    temp_path = ""
    try:
        temp_path = _write_temp_note(kind, topic, summary, facts, decisions, preferences, next_actions)
        payload = build_payload(repo_root, kind, topic, summary, facts, decisions, preferences, next_actions)
        payload["path"] = temp_path

        req = request.Request(
            f"{base_url}{RESOURCES_ENDPOINT}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        resp = request.urlopen(req, timeout=REQUEST_TIMEOUT)
        body = json.loads(resp.read().decode("utf-8"))

        result = body.get("result", {})
        if result.get("status") == "success":
            return {
                "status": "committed",
                "uri": result.get("root_uri"),
                "detail": f"mode=direct_http, kind={kind}",
                "errors": result.get("errors", []),
            }
        return {
            "status": "skipped_or_failed",
            "uri": None,
            "detail": f"upload failed: {result.get('errors', result)}",
        }
    except URLError as e:
        return {
            "status": "skipped_or_failed",
            "uri": None,
            "detail": f"connection failed: {e.reason}",
        }
    except Exception as e:
        return {
            "status": "skipped_or_failed",
            "uri": None,
            "detail": f"unexpected error: {e}",
        }
    finally:
        if temp_path:
            try:
                import sys
_script_dir = Path(__file__).resolve().parent
_jarvis_root = _script_dir.parent.parent
if str(_jarvis_root) not in sys.path:
    sys.path.insert(0, str(_jarvis_root))

from jarvis.lib import trash_path
                trash_path(temp_path)
            except Exception:
                pass


def format_result(response: dict) -> dict:
    """Normalize the response into the committed/skipped_or_failed contract."""
    return response


def should_attempt(base_url: str = DEFAULT_BASE_URL) -> bool:
    """Check if OpenViking HTTP API is reachable."""
    try:
        req = request.Request(f"{base_url}/health", method="GET")
        resp = request.urlopen(req, timeout=5)
        return json.loads(resp.read().decode("utf-8")).get("status") == "ok"
    except Exception:
        return False


def build_downgrade_record(reason: str = "memcommit not attempted") -> dict:
    """Build a downgrade record when memcommit is skipped."""
    return {
        "status": "skipped_or_failed",
        "detail": reason,
        "uri": None,
        "memory_commit": "skipped_or_failed",
    }


# ── CLI ─────────────────────────────────────────────────────────


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="OpenViking memcommit adapter")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--kind", default="topic_update")
    parser.add_argument("--topic", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--fact", action="append", default=[])
    parser.add_argument("--decision", action="append", default=[])
    parser.add_argument("--preference", action="append", default=[])
    parser.add_argument("--next-action", action="append", default=[])
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--check-health", action="store_true")
    parser.add_argument("--write", action="store_true", help="Actually write to OpenViking. Default is dry-run (payload only).")
    args = parser.parse_args()

    if args.check_health:
        ok = should_attempt(args.base_url)
        print(json.dumps({"health": "ok" if ok else "unreachable"}, ensure_ascii=False))
        print("validation result:")
        print("- passed" if ok else "- warning: OpenViking unreachable")
        return 0

    payload = build_payload(
        repo_root=args.repo_root,
        kind=args.kind,
        topic=args.topic,
        summary=args.summary,
        facts=args.fact,
        decisions=args.decision,
        preferences=args.preference,
        next_actions=args.next_action,
    )

    if not args.write:
        print("mode: dry-run")
        print("plan:")
        print(f"- would POST to: {payload['to']}")
        print(f"- topic: {args.topic}")
        print(f"- facts: {len(args.fact)}, decisions: {len(args.decision)}")
        print("\npayload preview:")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("\nvalidation result:")
        print("- passed")
        return 0

    result = commit_memory(
        repo_root=args.repo_root,
        kind=args.kind,
        topic=args.topic,
        summary=args.summary,
        facts=args.fact,
        decisions=args.decision,
        preferences=args.preference,
        next_actions=args.next_action,
        base_url=args.base_url,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("validation result:")
    print("- passed" if result["status"] == "committed" else "- failed: " + result.get("detail", "unknown"))
    return 0 if result["status"] == "committed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
