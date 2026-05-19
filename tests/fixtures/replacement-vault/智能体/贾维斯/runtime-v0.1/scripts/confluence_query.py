#!/usr/bin/env python3
"""Read or search Confluence using the local cookie file."""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

from jarvis_lib import print_validation, write_json_result


def load_cookie(cookie_file: Path) -> str:
    return cookie_file.read_text(encoding="utf-8").strip()


def build_url(base_url: str, mode: str, page_id: str, query: str) -> str:
    if mode == "read-page":
        return f"{base_url.rstrip('/')}/rest/api/content/{page_id}?expand=body.storage"
    cql = ""
    if mode == "search-title":
        cql = f'title~"{query}"'
    elif mode == "search-text":
        cql = f'text~"{query}" AND type=page'
    elif mode == "search-comments":
        cql = f'type=comment AND text~"{query}"'
    else:
        raise ValueError(mode)
    return f"{base_url.rstrip('/')}/rest/api/content/search?cql={urllib.parse.quote(cql)}"


def request_json(url: str, cookie: str) -> tuple[int, dict | str]:
    request = urllib.request.Request(url, headers={"Cookie": cookie, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status = response.getcode()
            body = response.read().decode("utf-8", errors="ignore")
            try:
                return status, json.loads(body)
            except json.JSONDecodeError:
                return status, body
    except urllib.error.HTTPError as exc:  # type: ignore[name-defined]
        body = exc.read().decode("utf-8", errors="ignore")
        return exc.code, body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["validate-config", "read-page", "search-title", "search-text", "search-comments"])
    parser.add_argument("--base-url", default="https://www.kf580.com/kd")
    parser.add_argument("--cookie-file", default="platform-ops/.confluence-cookie")
    parser.add_argument("--page-id", default="")
    parser.add_argument("--query", default="")
    args = parser.parse_args()

    cookie_file = Path(args.cookie_file).expanduser().resolve()
    print("plan:")
    print(f"- confluence mode: {args.mode}")
    print(f"- base url: {args.base_url}")
    print(f"- cookie file: {cookie_file}")
    print("\ndiff preview:")
    print("(read-only)")

    if not cookie_file.exists():
        return print_validation([f"cookie file not found: {cookie_file}"])
    cookie = load_cookie(cookie_file)
    if not cookie:
        return print_validation([f"cookie file is empty: {cookie_file}"])
    if args.mode == "validate-config":
        write_json_result({"base_url": args.base_url, "cookie_file": str(cookie_file), "cookie_length": len(cookie)})
        return print_validation([])
    if args.mode == "read-page" and not args.page_id:
        return print_validation(["--page-id is required for read-page"])
    if args.mode != "read-page" and not args.query:
        return print_validation(["--query is required for search modes"])

    url = build_url(args.base_url, args.mode, args.page_id, args.query)
    status, payload = request_json(url, cookie)
    write_json_result({"status": status, "url": url, "payload": payload})
    if status in (401, 403):
        return print_validation(["Confluence cookie expired or insufficient permissions"])
    if status == 404:
        return print_validation(["Confluence page not found"])
    if status >= 400:
        return print_validation([f"Confluence request failed with status {status}"])
    return print_validation([])


if __name__ == "__main__":
    raise SystemExit(main())
