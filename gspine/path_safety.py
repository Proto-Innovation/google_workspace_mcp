"""Resolve caller paths against a connector's account root, refusing any path
that escapes it. This is the in-process confidentiality boundary: one connector
instance serves one account folder and can touch nothing else in the repo."""

import posixpath


def safe_repo_path(root: str, rel: str) -> str:
    if rel.startswith("/"):
        raise ValueError(f"Absolute paths are not allowed: {rel!r}")
    root_norm = posixpath.normpath(root) if root else ""
    if root_norm == ".":
        root_norm = ""
    joined = posixpath.normpath(posixpath.join(root_norm, rel))
    if joined == ".." or joined.startswith("../"):
        raise ValueError(f"Path escapes the connector root: {rel!r}")
    if root_norm and joined != root_norm and not joined.startswith(root_norm + "/"):
        raise ValueError(f"Path escapes the connector root: {rel!r}")
    return joined
