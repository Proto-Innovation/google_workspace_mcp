import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from unittest.mock import AsyncMock, patch


def _unwrap(tool):
    fn = tool.fn if hasattr(tool, "fn") else tool
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


@pytest.mark.asyncio
async def test_append_creates_stamped_entry(monkeypatch):
    monkeypatch.setenv("GSPINE_GITHUB_TOKEN", "tok")
    monkeypatch.setenv("GSPINE_REPO", "Proto-Innovation/spine")
    monkeypatch.setenv("GSPINE_DEFAULT_BRANCH", "main")
    monkeypatch.setenv("GSPINE_PATH_ROOT", "projects/clients/powerschool")
    from gspine import spine_tools

    with patch("gspine.spine_tools._utcnow_iso", return_value="2026-07-05T14:30:07"), \
         patch("gspine.spine_tools.resolve_author_email",
               new_callable=AsyncMock, return_value="jonathan.greene@wearepro.to"), \
         patch("gspine.spine_tools.github_client.put_file",
               new_callable=AsyncMock) as mock_put:
        mock_put.return_value = {"commit": {"sha": "abc1234def"}}
        out = await _unwrap(spine_tools.spine_append_log)(
            entry_type="decision", body="Service account for writes.")

    kwargs = mock_put.call_args.kwargs
    assert kwargs["path"] == \
        "projects/clients/powerschool/log/2026-07-05-143007-jonathan.greene-decision.md"
    assert "author_email: jonathan.greene@wearepro.to" in kwargs["text"]
    assert "type: decision" in kwargs["text"]
    assert kwargs["committer_name"] == "Proto Automation"
    assert kwargs["branch"] == "main"
    assert "abc1234" in out


@pytest.mark.asyncio
async def test_append_rejects_unknown_type(monkeypatch):
    monkeypatch.setenv("GSPINE_GITHUB_TOKEN", "tok")
    monkeypatch.setenv("GSPINE_REPO", "Proto-Innovation/spine")
    monkeypatch.setenv("GSPINE_PATH_ROOT", "projects/clients/powerschool")
    from gspine import spine_tools
    with patch("gspine.spine_tools.resolve_author_email",
               new_callable=AsyncMock, return_value="a@b.com"):
        with pytest.raises(ValueError):
            await _unwrap(spine_tools.spine_append_log)(entry_type="oops", body="x")
