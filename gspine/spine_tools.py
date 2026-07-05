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
    return os.getenv("GSPINE_PATH_ROOT", config.GSPINE_PATH_ROOT)


def _token() -> str:
    return _require("GSPINE_GITHUB_TOKEN", os.getenv("GSPINE_GITHUB_TOKEN"))


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
    return await github_client.get_contents(
        repo=_repo(), path=safe, ref=_branch(), token=_token())
