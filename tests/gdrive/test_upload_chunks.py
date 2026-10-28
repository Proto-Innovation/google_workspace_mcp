"""upload_drive_file_chunk: a client that can't reach Google directly (a claude.ai
artifact page) sends a file in base64 pieces; the server forwards each piece to a
Drive resumable session opened by create_drive_file(return_upload_url=True).

Pinned here: only Google's Drive upload endpoint is ever contacted (no SSRF), the
bytes go through untouched with the right Content-Range and no Authorization
header, and the reply tells the client where to resume or the new file's ID.
"""

import base64
import json

import httpx
import pytest

from core.tool_tier_loader import ToolTierLoader
from core.utils import UserInputError
from gdrive import drive_tools
from gdrive.drive_tools import upload_drive_file_chunk

SESSION = "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&supportsAllDrives=true&upload_id=ABC"
CHUNK = 256 * 1024


def _unwrap(tool):
    fn = tool.fn if hasattr(tool, "fn") else tool
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _transport(monkeypatch, handler, seen):
    real_client = drive_tools.httpx.AsyncClient

    def record(request):
        seen.append(request)
        return handler(request)

    monkeypatch.setattr(
        drive_tools.httpx,
        "AsyncClient",
        lambda **kw: real_client(transport=httpx.MockTransport(record), **kw),
    )


async def _call(**kw):
    args = dict(upload_url=SESSION, offset=0, total_size=CHUNK * 3, chunk_base64="")
    args.update(kw)
    return await _unwrap(upload_drive_file_chunk)(**args)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/upload/drive/v3/files?upload_id=ABC",
        "http://www.googleapis.com/upload/drive/v3/files?upload_id=ABC",
        "https://www.googleapis.com/drive/v3/files?upload_id=ABC",
        "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable",
        "https://www.googleapis.com.evil.example/upload/drive/v3/files?upload_id=ABC",
    ],
)
async def test_rejects_anything_but_a_drive_upload_session(url):
    with pytest.raises(UserInputError, match="Drive resumable upload session URL"):
        await _call(
            upload_url=url, chunk_base64=base64.b64encode(b"x" * CHUNK).decode()
        )


@pytest.mark.asyncio
async def test_rejects_invalid_base64():
    with pytest.raises(UserInputError, match="chunk_base64 is not valid base64"):
        await _call(chunk_base64="not base64!!")


@pytest.mark.asyncio
async def test_rejects_chunk_past_total():
    data = base64.b64encode(b"x" * CHUNK).decode()
    with pytest.raises(UserInputError, match="runs past total_size"):
        await _call(offset=CHUNK * 3, chunk_base64=data)


@pytest.mark.asyncio
async def test_rejects_non_final_chunk_off_the_256k_grid():
    data = base64.b64encode(b"x" * 1000).decode()
    with pytest.raises(UserInputError, match="multiple of 262144"):
        await _call(chunk_base64=data)


@pytest.mark.asyncio
async def test_forwards_bytes_and_reports_next_offset(monkeypatch):
    seen = []
    _transport(
        monkeypatch,
        lambda r: httpx.Response(308, headers={"Range": f"bytes=0-{CHUNK - 1}"}),
        seen,
    )
    raw = bytes(range(256)) * (CHUNK // 256)
    out = json.loads(await _call(chunk_base64=base64.b64encode(raw).decode()))
    assert out == {"status": "incomplete", "next_offset": CHUNK}
    (req,) = seen
    assert req.method == "PUT"
    assert str(req.url) == SESSION
    assert req.headers["Content-Range"] == f"bytes 0-{CHUNK - 1}/{CHUNK * 3}"
    assert "Authorization" not in req.headers
    assert req.content == raw


@pytest.mark.asyncio
async def test_final_chunk_returns_the_new_file(monkeypatch):
    seen = []
    _transport(
        monkeypatch,
        lambda r: httpx.Response(
            200, json={"id": "F1", "name": "animation.gif", "mimeType": "image/gif"}
        ),
        seen,
    )
    raw = b"g" * 100
    out = json.loads(
        await _call(
            offset=CHUNK * 2,
            total_size=CHUNK * 2 + 100,
            chunk_base64=base64.b64encode(raw).decode(),
        )
    )
    assert out == {"status": "complete", "file_id": "F1", "name": "animation.gif"}
    assert (
        seen[0].headers["Content-Range"]
        == f"bytes {CHUNK * 2}-{CHUNK * 2 + 99}/{CHUNK * 2 + 100}"
    )


@pytest.mark.asyncio
async def test_expired_session_is_a_clear_error(monkeypatch):
    _transport(monkeypatch, lambda r: httpx.Response(404, text="Not Found"), [])
    with pytest.raises(UserInputError, match="upload session is no longer valid"):
        await _call(chunk_base64=base64.b64encode(b"x" * CHUNK).decode())


def test_tool_in_drive_extended_tier():
    tools = ToolTierLoader().get_tools_for_tier("extended", services=["drive"])
    assert "upload_drive_file_chunk" in tools
