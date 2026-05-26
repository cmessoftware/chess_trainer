import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib import error, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create parent/child Gitea issues from a roadmap issue pack JSON."
    )
    parser.add_argument(
        "--pack",
        required=True,
        help="Path to issue pack JSON (phase-01-core-engine-minimal-api-gitea-issues.json).",
    )
    parser.add_argument(
        "--roadmap",
        default="",
        help="Optional roadmap markdown file to update with created issue numbers.",
    )
    parser.add_argument(
        "--mapping-output",
        default="",
        help="Optional JSON path for created issue mapping. Defaults next to pack.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without creating issues.",
    )
    return parser.parse_args()


def env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def gitea_request(
    base_url: str,
    token: str,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Any:
    url = f"{base_url.rstrip('/')}/api/v1{path}"
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    # Some Gitea setups accept only one of these auth styles.
    auth_headers = [f"token {token}", f"Bearer {token}"]
    last_exc: Optional[Exception] = None

    for auth_value in auth_headers:
        headers = {
            "Authorization": auth_value,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        req = request.Request(url=url, data=body, headers=headers, method=method)
        try:
            with request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            last_exc = RuntimeError(
                f"Gitea API {method} {path} failed: HTTP {exc.code} {exc.reason}. Details: {details}"
            )
            # Retry with alternative header style on auth errors.
            if exc.code in (401, 403):
                continue
            raise last_exc

    if last_exc is not None:
        raise last_exc

    raise RuntimeError(f"Gitea API {method} {path} failed with unknown error")


def load_label_map(base_url: str, token: str, owner: str, repo: str) -> Dict[str, int]:
    labels = gitea_request(base_url, token, "GET", f"/repos/{owner}/{repo}/labels")
    mapping: Dict[str, int] = {}
    for label in labels:
        name = label.get("name")
        label_id = label.get("id")
        if isinstance(name, str) and isinstance(label_id, int):
            mapping[name] = label_id
    return mapping


def build_issue_body(
    issue: Dict[str, Any],
    openspec_change: str,
    parent_number: Optional[int],
) -> str:
    lines: List[str] = []
    lines.append("## Context")
    lines.append("Created from roadmap issue pack for Phase 1.")
    lines.append("")
    if issue.get("feat"):
        lines.append(f"- feat: {issue['feat']}")
    lines.append(f"- key: {issue.get('key', 'UNKNOWN')}")
    lines.append(f"- openspec_change: {openspec_change}")

    metadata = issue.get("metadata", {})
    if isinstance(metadata, dict) and metadata:
        lines.append("")
        lines.append("## Metadata")
        for k in ["alias", "domain", "phase", "owner"]:
            if metadata.get(k):
                lines.append(f"- {k}: {metadata[k]}")

    if parent_number is not None:
        lines.append("")
        lines.append("## Relationship")
        lines.append(f"- parent_issue: #{parent_number}")

    lines.append("")
    lines.append("## Checklist")
    lines.append("- [ ] Define acceptance criteria")
    lines.append("- [ ] Implement")
    lines.append("- [ ] Add tests")
    lines.append("- [ ] Update docs and roadmap")

    return "\n".join(lines)


def create_issue(
    base_url: str,
    token: str,
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels_by_name: List[str],
    label_map: Dict[str, int],
    dry_run: bool,
) -> Dict[str, Any]:
    label_ids = [label_map[name] for name in labels_by_name if name in label_map]
    unknown_labels = [name for name in labels_by_name if name not in label_map]

    payload = {
        "title": title,
        "body": body,
    }
    if label_ids:
        payload["labels"] = label_ids

    if dry_run:
        print(f"[DRY-RUN] Would create issue: {title}")
        if unknown_labels:
            print(f"[DRY-RUN] Unknown labels skipped: {unknown_labels}")
        return {
            "number": None,
            "html_url": None,
            "unknown_labels": unknown_labels,
            "payload": payload,
        }

    created = gitea_request(
        base_url,
        token,
        "POST",
        f"/repos/{owner}/{repo}/issues",
        payload,
    )
    created["unknown_labels"] = unknown_labels
    return created


def update_roadmap_with_numbers(
    roadmap_path: Path,
    key_to_number: Dict[str, int],
) -> None:
    content = roadmap_path.read_text(encoding="utf-8")

    parent_no = key_to_number.get("P1-EPIC-CORE-API")
    for child_key in ["P1-CH-01", "P1-CH-02", "P1-CH-03", "P1-CH-04"]:
        if child_key in key_to_number:
            replacement = f"#{key_to_number[child_key]}"
            if parent_no:
                replacement = f"#{key_to_number[child_key]} (parent: #{parent_no})"
            content = re.sub(
                rf"\b{re.escape(child_key)}\s*\(parent:\s*P1-EPIC-CORE-API\)",
                replacement,
                content,
            )

    roadmap_path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    pack_path = Path(args.pack)
    if not pack_path.exists():
        print(f"Pack file not found: {pack_path}")
        return 1

    data = json.loads(pack_path.read_text(encoding="utf-8"))
    issues = data.get("issues", [])
    openspec_change = data.get("openspec_change", "unknown")
    if not isinstance(issues, list) or not issues:
        print("Invalid issue pack: missing issues array")
        return 1

    base_url = os.getenv("GITEA_BASE_URL", "").strip()
    token = os.getenv("GITEA_TOKEN", "").strip()
    owner = os.getenv("GITEA_OWNER", "").strip()
    repo = os.getenv("GITEA_REPO", "").strip()

    if not args.dry_run:
        try:
            if not base_url:
                base_url = env_required("GITEA_BASE_URL")
            if not token:
                token = env_required("GITEA_TOKEN")
            if not owner:
                owner = env_required("GITEA_OWNER")
            if not repo:
                repo = env_required("GITEA_REPO")
        except ValueError as exc:
            print(str(exc))
            return 1
    else:
        base_url = base_url or "https://gitea.example.com"
        token = token or "dry-run-token"
        owner = owner or "owner"
        repo = repo or "repo"

    print(f"Using Gitea repo: {owner}/{repo}")
    label_map = {} if args.dry_run else load_label_map(base_url, token, owner, repo)

    parent = next((i for i in issues if i.get("type") == "parent"), None)
    if parent is None:
        print("Invalid issue pack: parent issue not found")
        return 1

    child_issues = [i for i in issues if i.get("type") == "child"]

    key_to_created: Dict[str, Dict[str, Any]] = {}
    key_to_number: Dict[str, int] = {}

    parent_body = build_issue_body(parent, openspec_change, parent_number=None)
    created_parent = create_issue(
        base_url,
        token,
        owner,
        repo,
        parent["title"],
        parent_body,
        parent.get("labels", []),
        label_map,
        args.dry_run,
    )
    key_to_created[parent["key"]] = created_parent
    parent_number = created_parent.get("number")
    if isinstance(parent_number, int):
        key_to_number[parent["key"]] = parent_number
        print(f"Created parent {parent['key']} -> #{parent_number}")
    else:
        print(f"Parent {parent['key']} prepared (dry-run)")

    for child in child_issues:
        body = build_issue_body(child, openspec_change, parent_number=parent_number)
        created_child = create_issue(
            base_url,
            token,
            owner,
            repo,
            child["title"],
            body,
            child.get("labels", []),
            label_map,
            args.dry_run,
        )
        key_to_created[child["key"]] = created_child
        number = created_child.get("number")
        if isinstance(number, int):
            key_to_number[child["key"]] = number
            print(f"Created child {child['key']} -> #{number}")
        else:
            print(f"Child {child['key']} prepared (dry-run)")

    if not args.dry_run and isinstance(parent_number, int):
        child_lines = []
        for child in child_issues:
            num = key_to_number.get(child.get("key", ""))
            if num:
                child_lines.append(f"- [ ] #{num} ({child['key']})")
        if child_lines:
            comment_body = "Linked child issues:\n\n" + "\n".join(child_lines)
            gitea_request(
                base_url,
                token,
                "POST",
                f"/repos/{owner}/{repo}/issues/{parent_number}/comments",
                {"body": comment_body},
            )
            print(f"Added child list comment to parent #{parent_number}")

    mapping_output = Path(args.mapping_output) if args.mapping_output else pack_path.with_name(
        f"{pack_path.stem}-created-mapping.json"
    )
    mapping_payload = {
        "source_pack": str(pack_path),
        "dry_run": args.dry_run,
        "repo": f"{owner}/{repo}",
        "openspec_change": openspec_change,
        "key_to_number": key_to_number,
        "created": key_to_created,
    }
    mapping_output.write_text(
        json.dumps(mapping_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Mapping written to: {mapping_output}")

    if args.roadmap and not args.dry_run and key_to_number:
        roadmap_path = Path(args.roadmap)
        if roadmap_path.exists():
            update_roadmap_with_numbers(roadmap_path, key_to_number)
            print(f"Roadmap updated with issue numbers: {roadmap_path}")
        else:
            print(f"Roadmap file not found, skipped update: {roadmap_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
