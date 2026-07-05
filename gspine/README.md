# gspine — project-spine git connector

Two MCP tools that let a claude.ai team-project chat read and append to a
git-backed project spine. Reads/writes are scoped to one account folder; the
GitHub write uses a service-account token; each entry is stamped with the
driving user's Google email.

## Tools
- `spine_read(path)` — read a file under the account root (e.g. `PROJECT.md`).
- `spine_append_log(entry_type, body, ...)` — create `log/<ts>-<author>-<type>.md`.

## Deploy: one connector instance per account

Set these env vars on the Cloud Run service (the token as a Secret Manager
secret, the rest as plain env):

| Var | Example | Notes |
|-----|---------|-------|
| `GSPINE_GITHUB_TOKEN` | `ghp_…` | Service-account PAT with `contents:write` on the repo. Secret. |
| `GSPINE_REPO` | `Proto-Innovation/proto-spines` | `owner/name`. Required. |
| `GSPINE_PATH_ROOT` | `projects/clients/powerschool` | The account folder. Isolation boundary. |
| `GSPINE_DEFAULT_BRANCH` | `main` | Optional; defaults to `main`. |
| `GSPINE_COMMITTER_NAME` | `Proto Automation` | Optional. |
| `GSPINE_COMMITTER_EMAIL` | `automation@wearepro.to` | Optional. |
| `GSPINE_ALLOW_REPO_ROOT` | (unset) | Set truthy ONLY to intentionally allow whole-repo access with no path prefix. Leave unset for account isolation. |

**Rebuild caveat:** any image rebuild must keep `--extra valkey` in the
Dockerfile `uv sync` line, or the OAuth session store falls back to in-memory
and connectors drop.

**Isolation:** `GSPINE_PATH_ROOT` is enforced in-process by `safe_repo_path`;
one account per connector instance. NDA-sensitive accounts must run their own
instance — never share a repo across accounts on a single instance without the
root set. An unset `GSPINE_PATH_ROOT` now fails closed (raises rather than
granting whole-repo access); set `GSPINE_ALLOW_REPO_ROOT=1` to opt in
intentionally.
