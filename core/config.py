"""
Shared configuration for Google Workspace MCP server.
This module holds configuration values that need to be shared across modules
to avoid circular imports.

NOTE: OAuth configuration has been moved to auth.oauth_config for centralization.
This module now imports from there for backward compatibility.
"""

import os
from typing import TYPE_CHECKING

from auth.oauth_config import (
    get_oauth_base_url,
    get_oauth_redirect_uri,
    set_transport_mode,
    get_transport_mode,
    is_oauth21_enabled,
)

# Server configuration. WORKSPACE_MCP_PORT is resolved lazily via PEP 562
# __getattr__ so that the value reflects the current env at access time.
# main.py mutates WORKSPACE_MCP_PORT in os.environ at startup via the port
# resolver (auth.port_resolver.resolve_port); consumers that do
# `from core.config import WORKSPACE_MCP_PORT` inside a function will see the
# late-bound port instead of a frozen-at-module-import 8000.
WORKSPACE_MCP_BASE_URI = os.getenv("WORKSPACE_MCP_BASE_URI", "http://localhost")
WORKSPACE_EXTERNAL_URL = os.getenv("WORKSPACE_EXTERNAL_URL")

if TYPE_CHECKING:
    WORKSPACE_MCP_PORT: int


def __getattr__(name: str) -> int:
    if name == "WORKSPACE_MCP_PORT":
        if os.getenv("WORKSPACE_MCP_RESOLVED_PORT") == "1":
            return int(os.getenv("WORKSPACE_MCP_PORT", os.getenv("PORT", "8000")))
        return int(os.getenv("PORT", os.getenv("WORKSPACE_MCP_PORT", "8000")))
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Disable USER_GOOGLE_EMAIL in OAuth 2.1 multi-user mode
USER_GOOGLE_EMAIL = (
    None if is_oauth21_enabled() else os.getenv("USER_GOOGLE_EMAIL", None)
)

# --- gspine (project-spine git connector) ---
GSPINE_REPO = os.getenv("GSPINE_REPO")                       # "owner/name"; required at call time
GSPINE_DEFAULT_BRANCH = os.getenv("GSPINE_DEFAULT_BRANCH", "main")
GSPINE_PATH_ROOT = os.getenv("GSPINE_PATH_ROOT", "")         # e.g. "projects/clients/powerschool"
GSPINE_COMMITTER_NAME = os.getenv("GSPINE_COMMITTER_NAME", "Proto Automation")
GSPINE_COMMITTER_EMAIL = os.getenv("GSPINE_COMMITTER_EMAIL", "automation@wearepro.to")
GSPINE_ALLOW_REPO_ROOT = os.getenv("GSPINE_ALLOW_REPO_ROOT")  # set truthy to intentionally allow repo-root (no path prefix)

# Re-export OAuth functions for backward compatibility
__all__ = [
    "WORKSPACE_MCP_PORT",
    "WORKSPACE_MCP_BASE_URI",
    "WORKSPACE_EXTERNAL_URL",
    "USER_GOOGLE_EMAIL",
    "GSPINE_REPO",
    "GSPINE_DEFAULT_BRANCH",
    "GSPINE_PATH_ROOT",
    "GSPINE_COMMITTER_NAME",
    "GSPINE_COMMITTER_EMAIL",
    "GSPINE_ALLOW_REPO_ROOT",
    "get_oauth_base_url",
    "get_oauth_redirect_uri",
    "set_transport_mode",
    "get_transport_mode",
]
