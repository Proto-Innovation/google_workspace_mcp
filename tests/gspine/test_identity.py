import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from gspine import identity


@pytest.mark.asyncio
async def test_falls_back_to_param_when_no_context():
    # get_context raises (no active request) → use the passed email
    with patch("gspine.identity.get_context", side_effect=RuntimeError("no ctx")):
        assert await identity.resolve_author_email("jg@wearepro.to") == "jg@wearepro.to"


@pytest.mark.asyncio
async def test_prefers_oauth21_context_identity():
    ctx = MagicMock()
    ctx.get_state = AsyncMock(return_value="ameena@wearepro.to")
    with patch("gspine.identity.get_context", return_value=ctx):
        # even if a param is passed, the authenticated context wins
        assert await identity.resolve_author_email("jg@wearepro.to") == "ameena@wearepro.to"


@pytest.mark.asyncio
async def test_raises_when_no_identity_anywhere():
    ctx = MagicMock()
    ctx.get_state = AsyncMock(return_value=None)
    with patch("gspine.identity.get_context", return_value=ctx):
        with pytest.raises(ValueError):
            await identity.resolve_author_email("")
