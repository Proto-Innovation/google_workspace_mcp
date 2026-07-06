"""MCP tools for the git-backed project spine. Reads and appends within one
account folder (GSPINE_PATH_ROOT). Writes commit under the service-account
token; each entry is stamped with the driving user's email."""

import logging
import os
from datetime import datetime, timezone

from mcp.types import ToolAnnotations

import core.config as config
from core.server import server
from gspine import github_client
from gspine.identity import resolve_author_email
from gspine.log_format import build_log_entry
from gspine.path_safety import safe_repo_path

logger = logging.getLogger(__name__)


def _require(name: str, value):
    if not value:
        raise ValueError(f"{name} is not configured for this connector instance.")
    return value


def _repo() -> str:
    return _require("GSPINE_REPO", os.getenv("GSPINE_REPO") or config.GSPINE_REPO)


def _branch() -> str:
    return os.getenv("GSPINE_DEFAULT_BRANCH", config.GSPINE_DEFAULT_BRANCH)


def _root() -> str:
    root = os.getenv("GSPINE_PATH_ROOT", config.GSPINE_PATH_ROOT)
    if not root and not (os.getenv("GSPINE_ALLOW_REPO_ROOT") or config.GSPINE_ALLOW_REPO_ROOT):
        raise ValueError(
            "GSPINE_PATH_ROOT is not set. Refusing whole-repo access; set the account "
            "root, or set GSPINE_ALLOW_REPO_ROOT=1 to intentionally use the repo root."
        )
    return root


def _token() -> str:
    return _require("GSPINE_GITHUB_TOKEN", os.getenv("GSPINE_GITHUB_TOKEN"))


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


@server.tool(
    title="Read Project Spine File",
    annotations=ToolAnnotations(
        readOnlyHint=True, destructiveHint=False,
        idempotentHint=True, openWorldHint=True,
    ),
)
async def spine_read(path: str, user_google_email: str = "") -> str:
    """Read a file from this engagement's project spine (git-backed).

    Args:
        path: repo path relative to the connector's account root, e.g.
            'PROJECT.md' or 'log/2026-07-05-143007-jg-decision.md'.
        user_google_email: the driving user's email (auto-filled).
    """
    logger.info(f"[spine_read] path={path!r}")
    safe = safe_repo_path(_root(), path)
    content = await github_client.get_contents(
        repo=_repo(), path=safe, ref=_branch(), token=_token())

    # Surface the authenticated reader so the model knows who it's talking to.
    # Best-effort ONLY: a read must never fail because identity is unresolvable
    # (single-user / unauthenticated), so we swallow the fail-closed raise here.
    try:
        reader = await resolve_author_email(user_google_email)
    except Exception:
        reader = None
    if reader:
        header = (
            f"[spine] Current user (authenticated): {reader}. This is who you "
            "are talking to. Do not assume they are anyone named in the file "
            "below — the spine names the team in the third person.\n\n"
        )
        return header + content
    return content


@server.tool(
    title="Append Project Spine Log Entry",
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False,
        idempotentHint=False, openWorldHint=True,
    ),
)
async def spine_append_log(
    entry_type: str,
    body: str,
    user_google_email: str = "",
    subproject: str = "",
    slug: str = "",
    kind: str = "",
    status: str = "",
    location: str = "",
) -> str:
    """Append a NEW entry to this engagement's project-spine log. Creates a new
    file log/<ts>-<author>-<type>.md and never edits existing files, so
    concurrent writers can't collide. The author is the driving user; the commit
    lands under the service account.

    Args:
        entry_type: decision | status | blocker | question | note | artifact
        body: the entry text — prose, standalone.
        subproject: optional subproject tag.
        slug, kind, status, location: only for entry_type == 'artifact'.
        user_google_email: the driving user's email (auto-filled).
    """
    author_email = await resolve_author_email(user_google_email)
    logger.info(f"[spine_append_log] type={entry_type!r} author={author_email!r}")
    relpath, content = build_log_entry(
        ts=_utcnow_iso(),
        author_email=author_email,
        entry_type=entry_type,
        body=body,
        subproject=subproject or None,
        slug=slug or None,
        kind=kind or None,
        status=status or None,
        location=location or None,
    )
    safe = safe_repo_path(_root(), relpath)
    result = await github_client.put_file(
        repo=_repo(), path=safe,
        message=f"spine({entry_type}): {author_email}",
        text=content, branch=_branch(), token=_token(),
        committer_name=os.getenv("GSPINE_COMMITTER_NAME", config.GSPINE_COMMITTER_NAME),
        committer_email=os.getenv("GSPINE_COMMITTER_EMAIL", config.GSPINE_COMMITTER_EMAIL),
    )
    sha = result.get("commit", {}).get("sha", "?")[:7]
    return f"Appended {safe} (commit {sha})"
