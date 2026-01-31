"""Water heater platform for OmniLogic Local integration.

This module provides water heater entities for controlling pool/spa heaters.

IMPORTANT: Temperature Unit Handling
------------------------------------
The OmniLogic API always returns heater temperatures in Fahrenheit,
regardless of the system's unit configuration. This is a documented
device behavior, not a bug. The integration correctly reports Fahrenheit
as the native unit, and Home Assistant will automatically convert for
display based on the user's preferences.

See: https://github.com/cryptk/haomnilogic-local/issues/96
See: https://github.com/cryptk/haomnilogic-local/issues/127
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal, cast

from pyomnilogic_local.models.telemetry import TelemetryBoW
from pyomnilogic_local.omnitypes import OmniType

from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, STATE_ON, UnitOfTemperature

from .const import DOMAIN, KEY_COORDINATOR
from .entity import OmniLogicEntity
from .helpers.temperature import validate_temperature
from .types.entity_index import EntityIndexHeater, EntityIndexHeaterEquip
from .utils import get_entities_of_hass_type

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OmniLogicCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the water heater platform."""

    coordinator = hass.data[DOMAIN][entry.entry_id][KEY_COORDINATOR]

    all_heaters = get_entities_of_hass_type(coordinator.data, "water_heater")

    virtual_heater = {system_id: data for system_id, data in all_heaters.items() if data.msp_config.omni_type == OmniType.VIRT_HEATER}
    heater_equipment_ids = [system_id for system_id, data in all_heaters.items() if data.msp_config.omni_type == OmniType.HEATER_EQUIP]

    entities = []
    for system_id, vheater in virtual_heater.items():
        _LOGGER.debug(
            "Configuring water heater with ID: %s, Name: %s",
            vheater.msp_config.system_id,
            vheater.msp_config.name,
        )
        entities.append(
            OmniLogicWaterHeaterEntity(
                coordinator=coordinator,
                context=system_id,
                heater_equipment_ids=heater_equipment_ids,
            )
        )

    async_add_entities(entities)


class OmniLogicWaterHeaterEntity(OmniLogicEntity[EntityIndexHeater], WaterHeaterEntity):
    """Water heater entity for OmniLogic pool/spa heaters.

    This entity controls the virtual heater, which manages the actual
    heater equipment (gas, electric, heat pump, or solar).

    Temperature Unit Note:
        The OmniLogic API always returns heater temperatures in Fahrenheit,
        regardless of the system's configured units. This is documented
        device behavior. Home Assistant automatically converts the display
        based on user preferences.

        See: https://github.com/cryptk/haomnilogic-local/issues/96
    """

    # OmniLogic API always returns heater temps in Fahrenheit - this is device behavior
    _attr_temperature_unit = UnitOfTemperature.FAHRENHEIT
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.OPERATION_MODE
        | WaterHeaterEntityFeature.ON_OFF
    )
    _attr_operation_list = [STATE_ON, STATE_OFF]
    _attr_name = "Heater"

    def __init__(self, coordinator: OmniLogicCoordinator, context: int, heater_equipment_ids: list[int]) -> None:
        """Initialize the water heater entity.

        Args:
            coordinator: The data update coordinator.
            context: The system ID of this virtual heater.
            heater_equipment_ids: List of system IDs for associated heater equipment.
        """
        super().__init__(
            coordinator,
            context=context,
        )
        self.heater_equipment_ids = heater_equipment_ids

    @property
    def temperature_unit(self) -> str:
        """Return the temperature unit (always Fahrenheit for OmniLogic heaters)."""
        return self._attr_temperature_unit

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature setpoint."""
        return self.data.msp_config.min_temp

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature setpoint."""
        return self.data.msp_config.max_temp

    @property
    def target_temperature(self) -> float | None:
        """Return the current target temperature."""
        return self.data.telemetry.current_set_point

    @property
    def current_temperature(self) -> float | None:
        """Return the current water temperature from the body of water."""
        bow_telemetry = self.get_telemetry_by_systemid(self.bow_id)
        if bow_telemetry is None:
            return None
        return validate_temperature(cast(TelemetryBoW, bow_telemetry).water_temp)

    @property
    def current_operation(self) -> str:
        """Return the current operation mode (on/off)."""
        return str(STATE_ON) if self.data.telemetry.enabled else str(STATE_OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the target temperature."""
        temperature = int(kwargs[ATTR_TEMPERATURE])
        await self.coordinator.omni_api.async_set_heater(
            self.bow_id,
            self.system_id,
            temperature,
            unit=self.temperature_unit,
        )
        self.set_telemetry({"current_set_point": temperature})

    async def async_set_operation_mode(self, operation_mode: Literal["on", "off"]) -> None:
        match operation_mode:
            case "on":
                await self.coordinator.omni_api.async_set_heater_enable(self.bow_id, self.system_id, True)
                self.set_telemetry({"enabled": "yes"})
            case "off":
                await self.coordinator.omni_api.async_set_heater_enable(self.bow_id, self.system_id, False)
                self.set_telemetry({"enabled": "no"})

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.async_set_operation_mode("on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.async_set_operation_mode("off")

    @property
    def extra_state_attributes(self) -> dict[str, str | int]:
        extra_state_attributes = super().extra_state_attributes | {"solar_set_point": self.data.msp_config.solar_set_point}
        for system_id in self.heater_equipment_ids:
            heater_equipment = cast(EntityIndexHeaterEquip, self.coordinator.data[system_id])
            prefix = f"omni_heater_{heater_equipment.msp_config.name.lower()}"
            extra_state_attributes = extra_state_attributes | {
                f"{prefix}_enabled": heater_equipment.msp_config.enabled,
                f"{prefix}_system_id": system_id,
                f"{prefix}_bow_id": heater_equipment.msp_config.bow_id,
                f"{prefix}_state": heater_equipment.telemetry.state.pretty(),
                f"{prefix}_sensor_temp": heater_equipment.telemetry.temp,
            }
        return extra_state_attributes
