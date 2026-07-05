"""Resolve which human is driving the current request, for the author stamp.
OAuth 2.1 multi-user: the email is in the FastMCP request context. Single-user
self-hosted: the connector injects it as the user_google_email argument."""

from fastmcp.server.dependencies import get_context


async def resolve_author_email(user_google_email: str | None) -> str:
    try:
        ctx = get_context()
        email = await ctx.get_state("authenticated_user_email")
        if email:
            return email
    except Exception:
        pass
    if user_google_email:
        return user_google_email
    raise ValueError(
        "Could not resolve the driving user's identity for attribution."
    )
