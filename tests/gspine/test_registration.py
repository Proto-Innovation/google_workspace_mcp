# tests/gspine/test_registration.py
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest


def test_spine_in_service_modules():
    import main
    assert main.SERVICE_MODULES.get("spine") == "gspine.spine_tools"


def test_spine_in_tool_tiers():
    import yaml
    with open(os.path.join(os.path.dirname(__file__), "../../core/tool_tiers.yaml")) as fh:
        tiers = yaml.safe_load(fh)
    assert "spine" in tiers
    assert "spine_read" in tiers["spine"]["core"]
    assert "spine_append_log" in tiers["spine"]["core"]


@pytest.mark.asyncio
async def test_tools_register_on_import():
    import gspine.spine_tools  # noqa: F401  (import = registration)
    from core.server import server
    names = {t.name for t in await server.list_tools()}
    assert {"spine_read", "spine_append_log"} <= names
