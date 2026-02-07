"""Test the OmniLogic Local config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from custom_components.omnilogic_local.config_flow import CannotConnect, OmniLogicTimeout
from custom_components.omnilogic_local.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "custom_components.omnilogic_local.config_flow.validate_input",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "ip_address": "1.1.1.1",
                "name": "Omnilogic",
                "port": 10444,
                "scan_interval": 10,
                "timeout": 5.0,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Omnilogic"
    assert result2["data"] == {
        "ip_address": "1.1.1.1",
        "name": "Omnilogic",
        "port": 10444,
        "scan_interval": 10,
        "timeout": 5.0,
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_timeout(hass: HomeAssistant) -> None:
    """Test we handle timeout error."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(
        "custom_components.omnilogic_local.config_flow.validate_input",
        side_effect=OmniLogicTimeout,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "ip_address": "1.1.1.1",
                "name": "Omnilogic",
                "port": 10444,
                "scan_interval": 10,
                "timeout": 5.0,
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "timeout"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(
        "custom_components.omnilogic_local.config_flow.validate_input",
        side_effect=CannotConnect,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "ip_address": "1.1.1.1",
                "name": "Omnilogic",
                "port": 10444,
                "scan_interval": 10,
                "timeout": 5.0,
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
