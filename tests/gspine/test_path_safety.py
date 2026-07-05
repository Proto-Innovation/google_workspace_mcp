import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from gspine.path_safety import safe_repo_path

ROOT = "projects/clients/powerschool"

def test_joins_relative_path_under_root():
    assert safe_repo_path(ROOT, "PROJECT.md") == "projects/clients/powerschool/PROJECT.md"

def test_joins_nested_log_path():
    assert safe_repo_path(ROOT, "log/2026-07-05-143007-jg-decision.md") == \
        "projects/clients/powerschool/log/2026-07-05-143007-jg-decision.md"

def test_empty_root_returns_normalized_rel():
    assert safe_repo_path("", "PROJECT.md") == "PROJECT.md"

def test_rejects_absolute_path():
    with pytest.raises(ValueError):
        safe_repo_path(ROOT, "/etc/passwd")

def test_rejects_parent_traversal_to_sibling_account():
    with pytest.raises(ValueError):
        safe_repo_path(ROOT, "../mediaocean/PROJECT.md")

def test_rejects_embedded_traversal():
    with pytest.raises(ValueError):
        safe_repo_path(ROOT, "log/../../../secrets.md")
