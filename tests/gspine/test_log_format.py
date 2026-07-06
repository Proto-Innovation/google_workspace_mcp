# tests/gspine/test_log_format.py
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from gspine.log_format import author_slug_from_email, build_log_entry

def test_author_slug_takes_local_part():
    assert author_slug_from_email("jonathan.greene@wearepro.to") == "jonathan.greene"

def test_author_slug_sanitizes_unusual_chars():
    assert author_slug_from_email("A+B.c@x.com") == "a-b.c"

def test_author_slug_rejects_empty_local_part():
    with pytest.raises(ValueError):
        author_slug_from_email("@wearepro.to")

def test_build_log_entry_filename_and_frontmatter():
    path, content = build_log_entry(
        ts="2026-07-05T14:30:07",
        author_email="jonathan.greene@wearepro.to",
        entry_type="decision",
        body="We picked the service account for writes.",
    )
    assert path == "log/2026-07-05-143007-jonathan.greene-decision.md"
    assert content.startswith("---\n")
    assert "ts: 2026-07-05T14:30:07\n" in content
    assert "author: jonathan.greene\n" in content
    assert "author_email: jonathan.greene@wearepro.to\n" in content
    assert "type: decision\n" in content
    assert content.rstrip().endswith("We picked the service account for writes.")

def test_build_log_entry_includes_subproject_when_given():
    _, content = build_log_entry(
        ts="2026-07-05T14:30:07", author_email="a@b.com",
        entry_type="note", body="x", subproject="source-map")
    assert "subproject: source-map\n" in content

def test_build_log_entry_artifact_fields():
    path, content = build_log_entry(
        ts="2026-07-05T15:40:00", author_email="a@b.com", entry_type="artifact",
        body="v2 shipped", slug="source-map", kind="doc", status="in-review",
        location="https://example.com/x")
    assert path == "log/2026-07-05-154000-a-artifact.md"
    for line in ("slug: source-map", "kind: doc", "status: in-review",
                 "location: https://example.com/x"):
        assert line + "\n" in content

def test_build_log_entry_rejects_unknown_type():
    with pytest.raises(ValueError):
        build_log_entry(ts="2026-07-05T14:30:07", author_email="a@b.com",
                        entry_type="rambling", body="x")
