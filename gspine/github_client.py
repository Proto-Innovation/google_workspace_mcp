"""Minimal async GitHub Contents API client (httpx). get_contents reads a file;
put_file creates a new file under the service-account token."""

import base64

import httpx

_API = "https://api.github.com"


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"}


async def get_contents(*, repo: str, path: str, ref: str, token: str) -> str:
    url = f"{_API}/repos/{repo}/contents/{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params={"ref": ref}, headers=_headers(token))
    resp.raise_for_status()
    return base64.b64decode(resp.json()["content"]).decode("utf-8")


async def put_file(*, repo: str, path: str, message: str, text: str, branch: str,
                   token: str, committer_name: str, committer_email: str) -> dict:
    url = f"{_API}/repos/{repo}/contents/{path}"
    payload = {
        "message": message,
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
        "branch": branch,
        "committer": {"name": committer_name, "email": committer_email},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.put(url, json=payload, headers=_headers(token))
    resp.raise_for_status()
    return resp.json()
