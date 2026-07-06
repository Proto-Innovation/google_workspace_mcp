"""Resolve which human is driving the current request, for the author stamp.
OAuth 2.1 multi-user: the email is in the FastMCP request context. Single-user
self-hosted: the connector injects it as the user_google_email argument."""

from fastmcp.server.dependencies import get_context


async def resolve_author_email(user_google_email: str | None) -> str:
    ctx = None
    try:
        ctx = get_context()
    except Exception:
        ctx = None
    if ctx is not None:
        # A context exists: trust ONLY the authenticated identity it carries.
        # If reading it errors, let that propagate (fail closed) rather than
        # falling back to the caller-supplied, spoofable parameter.
        email = await ctx.get_state("authenticated_user_email")
        if email:
            return email
    if user_google_email:
        return user_google_email
    raise ValueError(
        "Could not resolve the driving user's identity for attribution."
    )
