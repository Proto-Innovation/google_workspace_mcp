import os, sys, base64, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import httpx
import pytest
from gspine import github_client


def _patch_transport(monkeypatch, handler):
    real = httpx.AsyncClient
    monkeypatch.setattr(
        github_client.httpx, "AsyncClient",
        lambda *a, **k: real(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.asyncio
async def test_get_contents_decodes_base64(monkeypatch):
    def handler(request):
        assert request.method == "GET"
        assert request.url.path == "/repos/o/r/contents/projects/x/PROJECT.md"
        assert request.url.params["ref"] == "main"
        assert request.headers["Authorization"] == "Bearer tok"
        return httpx.Response(200, json={"content": base64.b64encode(b"hello spine").decode()})

    _patch_transport(monkeypatch, handler)
    out = await github_client.get_contents(
        repo="o/r", path="projects/x/PROJECT.md", ref="main", token="tok")
    assert out == "hello spine"


@pytest.mark.asyncio
async def test_get_contents_raises_on_404(monkeypatch):
    _patch_transport(monkeypatch, lambda req: httpx.Response(404, json={"message": "Not Found"}))
    with pytest.raises(httpx.HTTPStatusError):
        await github_client.get_contents(repo="o/r", path="missing.md", ref="main", token="t")


@pytest.mark.asyncio
async def test_put_file_creates_without_sha(monkeypatch):
    captured = {}

    def handler(request):
        assert request.method == "PUT"
        assert request.url.path == "/repos/o/r/contents/projects/x/log/e.md"
        body = json.loads(request.content)
        captured.update(body)
        return httpx.Response(201, json={"commit": {"sha": "abc1234def"}})

    _patch_transport(monkeypatch, handler)
    result = await github_client.put_file(
        repo="o/r", path="projects/x/log/e.md", message="spine(note): a@b.com",
        text="hello", branch="main", token="tok",
        committer_name="Proto Automation", committer_email="automation@wearepro.to")

    assert result["commit"]["sha"] == "abc1234def"
    assert "sha" not in captured                      # create, not update
    assert base64.b64decode(captured["content"]) == b"hello"
    assert captured["branch"] == "main"
    assert captured["committer"] == {"name": "Proto Automation",
                                     "email": "automation@wearepro.to"}
