"""Turn a resolved identity + fields into an append-log entry: a unique
filename (ts+author+type, so two writers never collide) and the markdown body
with YAML frontmatter matching the project-os spine format."""

import re

_ALLOWED_TYPES = {"decision", "status", "blocker", "question", "note", "artifact"}


def author_slug_from_email(email: str) -> str:
    local = email.split("@", 1)[0].strip().lower()
    slug = re.sub(r"[^a-z0-9._-]", "-", local)
    if not slug:
        raise ValueError(f"Cannot derive an author slug from email: {email!r}")
    return slug


def build_log_entry(
    *,
    ts: str,
    author_email: str,
    entry_type: str,
    body: str,
    subproject: str | None = None,
    slug: str | None = None,
    kind: str | None = None,
    status: str | None = None,
    location: str | None = None,
) -> tuple[str, str]:
    if entry_type not in _ALLOWED_TYPES:
        raise ValueError(
            f"Unknown entry type {entry_type!r}; allowed: {sorted(_ALLOWED_TYPES)}"
        )
    author = author_slug_from_email(author_email)
    date, _, time = ts.partition("T")
    ts_compact = f"{date}-{time.replace(':', '')}"
    filename = f"log/{ts_compact}-{author}-{entry_type}.md"

    fm = [
        f"ts: {ts}",
        f"author: {author}",
        f"author_email: {author_email}",
        f"type: {entry_type}",
    ]
    if subproject:
        fm.append(f"subproject: {subproject}")
    if entry_type == "artifact":
        for key, val in (("slug", slug), ("kind", kind),
                         ("status", status), ("location", location)):
            if val:
                fm.append(f"{key}: {val}")

    content = "---\n" + "\n".join(fm) + "\n---\n" + body.rstrip() + "\n"
    return filename, content
