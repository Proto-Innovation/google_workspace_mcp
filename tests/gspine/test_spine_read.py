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
async def test_spine_read_resolves_root_and_returns_content(monkeypatch):
    monkeypatch.setenv("GSPINE_GITHUB_TOKEN", "tok")
    monkeypatch.setenv("GSPINE_REPO", "Proto-Innovation/spine")
    monkeypatch.setenv("GSPINE_DEFAULT_BRANCH", "main")
    monkeypatch.setenv("GSPINE_PATH_ROOT", "projects/clients/powerschool")
    from gspine import spine_tools

    with patch("gspine.spine_tools.github_client.get_contents",
               new_callable=AsyncMock) as mock_get:
        mock_get.return_value = "# PowerSchool spine\n"
        out = await _unwrap(spine_tools.spine_read)(path="PROJECT.md")

    assert out == "# PowerSchool spine\n"
    kwargs = mock_get.call_args.kwargs
    assert kwargs["repo"] == "Proto-Innovation/spine"
    assert kwargs["ref"] == "main"
    assert kwargs["path"] == "projects/clients/powerschool/PROJECT.md"


@pytest.mark.asyncio
async def test_spine_read_rejects_path_escape(monkeypatch):
    monkeypatch.setenv("GSPINE_GITHUB_TOKEN", "tok")
    monkeypatch.setenv("GSPINE_REPO", "Proto-Innovation/spine")
    monkeypatch.setenv("GSPINE_PATH_ROOT", "projects/clients/powerschool")
    from gspine import spine_tools
    with pytest.raises(ValueError):
        await _unwrap(spine_tools.spine_read)(path="../mediaocean/PROJECT.md")


@pytest.mark.asyncio
async def test_spine_read_requires_token(monkeypatch):
    monkeypatch.delenv("GSPINE_GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GSPINE_REPO", "Proto-Innovation/spine")
    monkeypatch.setenv("GSPINE_PATH_ROOT", "projects/clients/powerschool")
    from gspine import spine_tools
    with pytest.raises(ValueError):
        await _unwrap(spine_tools.spine_read)(path="PROJECT.md")


@pytest.mark.asyncio
async def test_spine_read_root_unset_fails_closed(monkeypatch):
    monkeypatch.setenv("GSPINE_GITHUB_TOKEN", "tok")
    monkeypatch.setenv("GSPINE_REPO", "Proto-Innovation/spine")
    monkeypatch.delenv("GSPINE_PATH_ROOT", raising=False)
    monkeypatch.delenv("GSPINE_ALLOW_REPO_ROOT", raising=False)
    from gspine import spine_tools
    # core.config is a cached module: an earlier test's monkeypatch.setenv
    # (before spine_tools' first import) can freeze GSPINE_PATH_ROOT non-empty
    # at module scope. Force the frozen default back to "" so this test is
    # order-independent.
    monkeypatch.setattr(spine_tools.config, "GSPINE_PATH_ROOT", "")
    with pytest.raises(ValueError):
        await _unwrap(spine_tools.spine_read)(path="PROJECT.md")


@pytest.mark.asyncio
async def test_spine_read_root_unset_allowed_with_optin(monkeypatch):
    monkeypatch.setenv("GSPINE_GITHUB_TOKEN", "tok")
    monkeypatch.setenv("GSPINE_REPO", "Proto-Innovation/spine")
    monkeypatch.delenv("GSPINE_PATH_ROOT", raising=False)
    monkeypatch.setenv("GSPINE_ALLOW_REPO_ROOT", "1")
    from gspine import spine_tools
    monkeypatch.setattr(spine_tools.config, "GSPINE_PATH_ROOT", "")
    with patch("gspine.spine_tools.github_client.get_contents",
               new_callable=AsyncMock) as mock_get:
        mock_get.return_value = "root ok\n"
        out = await _unwrap(spine_tools.spine_read)(path="PROJECT.md")
    assert out == "root ok\n"
    assert mock_get.call_args.kwargs["path"] == "PROJECT.md"
