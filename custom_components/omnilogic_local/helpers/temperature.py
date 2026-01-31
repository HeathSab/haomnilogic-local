"""Centralized temperature handling for OmniLogic Local integration.

This module provides consistent temperature unit detection and validation
across all temperature-related entities in the integration.

Temperature Unit Sources:
- SENSOR: Per-sensor configuration (used by temperature sensors)
- SYSTEM: System-wide configuration (used by solar set point)
- HEATER_API: Hardcoded Fahrenheit (OmniLogic API always returns heater temps in Fahrenheit)
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from homeassistant.const import UnitOfTemperature
from pyomnilogic_local.omnitypes import SensorUnits

if TYPE_CHECKING:
    from pyomnilogic_local.models.mspconfig import MSPSystem


class TemperatureSource(Enum):
    """Indicates how temperature unit should be determined.

    SENSOR: Use per-sensor configuration (SensorUnits enum)
    SYSTEM: Use system-wide configuration ("Metric" string check)
    HEATER_API: Hardcoded Fahrenheit (device behavior - heaters always report in Fahrenheit)
    """

    SENSOR = "sensor"
    SYSTEM = "system"
    HEATER_API = "heater"


# Sentinel values that indicate invalid/unavailable temperature readings
# -1: Common invalid marker
# 255: Unsigned byte max (0xFF) - sensor not connected
# 65535: Unsigned 16-bit max (0xFFFF) - sensor error
INVALID_TEMP_VALUES: frozenset[int] = frozenset((-1, 255, 65535))


def get_unit_from_sensor(sensor_units: SensorUnits) -> str | None:
    """Get Home Assistant temperature unit from sensor configuration.

    Args:
        sensor_units: The SensorUnits enum value from the sensor's MSP config.

    Returns:
        The corresponding Home Assistant UnitOfTemperature constant,
        or None if the sensor unit is unknown.
    """
    match sensor_units:
        case SensorUnits.FAHRENHEIT:
            return UnitOfTemperature.FAHRENHEIT
        case SensorUnits.CELSIUS:
            return UnitOfTemperature.CELSIUS
        case _:
            return None


def get_unit_from_system(system_config: MSPSystem) -> str:
    """Get Home Assistant temperature unit from system-wide configuration.

    The OmniLogic system stores a "units" field that can be "Metric" or
    other values (typically "Standard" for imperial).

    Args:
        system_config: The MSPSystem configuration object.

    Returns:
        UnitOfTemperature.CELSIUS for metric systems,
        UnitOfTemperature.FAHRENHEIT otherwise.
    """
    return (
        UnitOfTemperature.CELSIUS
        if is_metric_system(system_config)
        else UnitOfTemperature.FAHRENHEIT
    )


def is_metric_system(system_config: MSPSystem) -> bool:
    """Check if the OmniLogic system is configured for metric units.

    Args:
        system_config: The MSPSystem configuration object.

    Returns:
        True if the system is set to metric, False otherwise.
    """
    return system_config.units == "Metric"


def validate_temperature(value: int | float | None) -> float | None:
    """Filter out invalid temperature sentinel values.

    The OmniLogic system uses certain sentinel values to indicate
    that a temperature sensor is unavailable or returning invalid data.

    Args:
        value: The raw temperature value from the API.

    Returns:
        The temperature as a float if valid, None if the value
        is a known sentinel/invalid value.
    """
    if value is None or value in INVALID_TEMP_VALUES:
        return None
    return float(value)
