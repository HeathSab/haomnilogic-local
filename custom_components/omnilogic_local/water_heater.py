from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal, cast

from pyomnilogic_local.models.telemetry import TelemetryBoW
from pyomnilogic_local.omnitypes import OmniType

from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, STATE_ON, UnitOfTemperature
from homeassistant.util.unit_conversion import TemperatureConverter

from . import OmniLogicConfigEntry
from .const import INVALID_TEMP_VALUES
from .entity import OmniLogicEntity
from .types.entity_index import EntityIndexHeater, EntityIndexHeaterEquip
from .utils import get_entities_of_hass_type

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OmniLogicCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: OmniLogicConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the water heater platform."""

    coordinator = entry.runtime_data.coordinator

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
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.ON_OFF
    )
    _attr_operation_list = [STATE_ON, STATE_OFF]
    _attr_name = "Heater"

    def __init__(self, coordinator: OmniLogicCoordinator, context: int, heater_equipment_ids: list[int]) -> None:
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(
            coordinator,
            context=context,
        )
        self.heater_equipment_ids = heater_equipment_ids

    @property
    def _is_metric(self) -> bool:
        return self.get_system_config().units == "Metric"

    def _f_to_native(self, value: float) -> float:
        """Convert a Fahrenheit value to the native unit (°C if Metric, °F if Standard)."""
        if self._is_metric:
            return round(TemperatureConverter.convert(value, UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS))
        return value

    @property
    def temperature_unit(self) -> str:
        # Heaters always report in Fahrenheit from the hardware.
        # We convert to °C ourselves when the system is Metric so that
        # HA's UI steps in clean 1°C increments instead of fractional °F-based values.
        if self._is_metric:
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    @property
    def min_temp(self) -> float:
        return self._f_to_native(self.data.msp_config.min_temp)

    @property
    def max_temp(self) -> float:
        return self._f_to_native(self.data.msp_config.max_temp)

    @property
    def target_temperature(self) -> float | None:
        if self.data.telemetry.current_set_point is None:
            return None
        return self._f_to_native(self.data.telemetry.current_set_point)

    @property
    def current_temperature(self) -> float | None:
        bow_telemetry = self.get_telemetry_by_systemid(self.bow_id)
        if bow_telemetry is None:
            return None
        current_temp = cast(TelemetryBoW, bow_telemetry).water_temp
        if current_temp in INVALID_TEMP_VALUES:
            return None
        return self._f_to_native(current_temp)

    @property
    def current_operation(self) -> str:
        return str(STATE_ON) if self.data.telemetry.enabled else str(STATE_OFF)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temp = kwargs[ATTR_TEMPERATURE]
        # Convert to °F for the hardware if the user is working in °C
        if self._is_metric:
            temp_f = round(TemperatureConverter.convert(temp, UnitOfTemperature.CELSIUS, UnitOfTemperature.FAHRENHEIT))
        else:
            temp_f = round(temp)
        await self.coordinator.omni_api.async_set_heater(
            self.bow_id,
            self.system_id,
            temp_f,
            unit=UnitOfTemperature.FAHRENHEIT,
        )
        # Store the °F value in telemetry since that's what the hardware uses
        self.set_telemetry({"current_set_point": temp_f})

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
