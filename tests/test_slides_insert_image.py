"""Tests for insert_slide_image_from_drive (deck-motion: private Drive GIFs onto slides via Apps Script)."""

from unittest.mock import Mock

import pytest

from auth.scopes import SCRIPT_EXTERNAL_REQUEST_SCOPE, get_scopes_for_tools
from core.tool_tier_loader import ToolTierLoader
from core.utils import UserInputError
from gslides.slides_tools import insert_slide_image_from_drive


def _unwrap(tool):
    """Unwrap FunctionTool + decorators to the original async function."""
    fn = tool.fn if hasattr(tool, "fn") else tool
    while hasattr(fn, "__wrapped__"):
        fn = fn.__wrapped__
    return fn


def _script_service(response):
    service = Mock()
    service.scripts.return_value.run.return_value.execute.return_value = response
    return service


async def _call(service, **overrides):
    kwargs = dict(
        service=service,
        user_google_email="user@example.com",
        presentation_id="pres",
        page_object_id="p",
        drive_file_id="file",
        left_emu=1,
        top_emu=2,
        width_emu=3,
        height_emu=4,
    )
    kwargs.update(overrides)
    return await _unwrap(insert_slide_image_from_drive)(**kwargs)


OK_RESULT = {
    "response": {
        "result": {
            "objectId": "img1",
            "mode": "inserted",
            "leftPt": 0,
            "topPt": 0,
            "widthPt": 320,
            "heightPt": 180,
        }
    }
}


@pytest.mark.asyncio
async def test_missing_script_id_raises(monkeypatch):
    monkeypatch.delenv("DECK_MOTION_SCRIPT_ID", raising=False)
    with pytest.raises(UserInputError, match="DECK_MOTION_SCRIPT_ID"):
        await _call(_script_service(OK_RESULT))


@pytest.mark.asyncio
async def test_rejects_non_positive_box(monkeypatch):
    monkeypatch.setenv("DECK_MOTION_SCRIPT_ID", "script-1")
    service = _script_service(OK_RESULT)
    with pytest.raises(UserInputError, match="width_emu must be a positive integer"):
        await _call(service, width_emu=0)
    service.scripts.return_value.run.assert_not_called()


@pytest.mark.asyncio
async def test_run_request_body(monkeypatch):
    monkeypatch.setenv("DECK_MOTION_SCRIPT_ID", "script-1")
    service = _script_service(OK_RESULT)
    await _call(service)
    service.scripts.return_value.run.assert_called_once_with(
        scriptId="script-1",
        body={
            "function": "insertMotionGif",
            "devMode": False,
            "parameters": [
                "pres",
                "p",
                "file",
                {"left": 1, "top": 2, "width": 3, "height": 4},
                None,
            ],
        },
    )


@pytest.mark.asyncio
async def test_replace_object_id_is_passed(monkeypatch):
    monkeypatch.setenv("DECK_MOTION_SCRIPT_ID", "script-1")
    service = _script_service(OK_RESULT)
    await _call(service, replace_object_id="old")
    body = service.scripts.return_value.run.call_args.kwargs["body"]
    assert body["parameters"][4] == "old"


@pytest.mark.asyncio
async def test_success_message(monkeypatch):
    monkeypatch.setenv("DECK_MOTION_SCRIPT_ID", "script-1")
    message = await _call(_script_service(OK_RESULT))
    assert "Inserted image img1" in message
    assert "mode: inserted" in message


@pytest.mark.asyncio
async def test_script_error_message(monkeypatch):
    monkeypatch.setenv("DECK_MOTION_SCRIPT_ID", "script-1")
    response = {
        "error": {
            "message": "Script error",
            "details": [{"errorMessage": "GIF is 60.0 MB; Slides limit is 50 MB"}],
        }
    }
    message = await _call(_script_service(response))
    assert message == "Insert failed: GIF is 60.0 MB; Slides limit is 50 MB"


def test_slides_scopes_include_script_run():
    assert SCRIPT_EXTERNAL_REQUEST_SCOPE in get_scopes_for_tools(["slides"])


def test_tool_in_slides_extended_tier():
    tools = ToolTierLoader().get_tools_for_tier("extended", services=["slides"])
    assert "insert_slide_image_from_drive" in tools
