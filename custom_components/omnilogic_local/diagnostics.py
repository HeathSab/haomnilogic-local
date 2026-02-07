"""Diagnostics support for OmniLogic Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant

from . import OmniLogicConfigEntry


async def async_get_config_entry_diagnostics(hass: HomeAssistant, config_entry: OmniLogicConfigEntry) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diag: dict[str, Any] = {}

    diag["config"] = config_entry.as_dict()

    coordinator = config_entry.runtime_data.coordinator
    diag["msp_config"] = coordinator.msp_config_xml
    diag["telemetry"] = coordinator.telemetry_xml
    diag["data"] = coordinator.data

    return async_redact_data(diag, [CONF_IP_ADDRESS])
