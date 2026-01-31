"""Entity index type definitions for OmniLogic Local integration.

This module provides strongly-typed dataclasses for entity data,
pairing MSP configuration with telemetry for each entity type.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Union

from pyomnilogic_local.models.mspconfig import (
    MSPCSAD,
    MSPBackyard,
    MSPBoW,
    MSPChlorinator,
    MSPChlorinatorEquip,
    MSPColorLogicLight,
    MSPFilter,
    MSPHeaterEquip,
    MSPPump,
    MSPRelay,
    MSPSchedule,
    MSPSensor,
    MSPVirtualHeater,
)
from pyomnilogic_local.models.telemetry import (
    TelemetryBackyard,
    TelemetryBoW,
    TelemetryChlorinator,
    TelemetryColorLogicLight,
    TelemetryCSAD,
    TelemetryFilter,
    TelemetryGroup,
    TelemetryHeater,
    TelemetryPump,
    TelemetryRelay,
    TelemetryValveActuator,
    TelemetryVirtualHeater,
)


@dataclass
class EntityIndexBackyard:
    """Entity data for the backyard (system-level) device."""

    msp_config: MSPBackyard
    telemetry: TelemetryBackyard


@dataclass
class EntityIndexBodyOfWater:
    """Entity data for a body of water (pool/spa)."""

    msp_config: MSPBoW
    telemetry: TelemetryBoW


@dataclass
class EntityIndexColorLogicLight:
    """Entity data for a ColorLogic light."""

    msp_config: MSPColorLogicLight
    telemetry: TelemetryColorLogicLight


@dataclass
class EntityIndexFilter:
    """Entity data for a filter/pump with variable speed control."""

    msp_config: MSPFilter
    telemetry: TelemetryFilter


@dataclass
class EntityIndexHeater:
    """Entity data for a virtual heater (heater control entity)."""

    msp_config: MSPVirtualHeater
    telemetry: TelemetryVirtualHeater


@dataclass
class EntityIndexHeaterEquip:
    """Entity data for heater equipment (physical heater hardware)."""

    msp_config: MSPHeaterEquip
    telemetry: TelemetryHeater


@dataclass
class EntityIndexChlorinator:
    """Entity data for a chlorinator."""

    msp_config: MSPChlorinator
    telemetry: TelemetryChlorinator


@dataclass
class EntityIndexCSAD:
    """Entity data for a CSAD (pH/ORP chemical controller)."""

    msp_config: MSPCSAD
    telemetry: TelemetryCSAD


@dataclass
class EntityIndexChlorinatorEquip:
    """Entity data for chlorinator equipment."""

    msp_config: MSPChlorinatorEquip
    telemetry: TelemetryChlorinator


@dataclass
class EntityIndexPump:
    """Entity data for a standalone pump."""

    msp_config: MSPPump
    telemetry: TelemetryPump


@dataclass
class EntityIndexRelay:
    """Entity data for a relay (high voltage or valve actuator control)."""

    msp_config: MSPRelay
    telemetry: TelemetryRelay


@dataclass
class EntityIndexSensor:
    """Entity data for a sensor (temperature, flow, etc.).

    Note: Sensors do not have telemetry - their readings come from
    the associated device (backyard, body of water, or heater equipment).
    """

    msp_config: MSPSensor
    telemetry: None


@dataclass
class EntityIndexValveActuator:
    """Entity data for a valve actuator."""

    msp_config: MSPRelay
    telemetry: TelemetryValveActuator


@dataclass
class EntityIndexSchedule:
    """Entity data for a schedule."""

    msp_config: MSPSchedule
    telemetry: None


@dataclass
class EntityIndexGroup:
    """Entity data for a group/scene."""

    msp_config: MSPSchedule  # Groups use schedule config structure
    telemetry: TelemetryGroup


# Union type for all possible entity index types
EntityIndexType = Union[
    EntityIndexBackyard,
    EntityIndexBodyOfWater,
    EntityIndexColorLogicLight,
    EntityIndexChlorinator,
    EntityIndexChlorinatorEquip,
    EntityIndexCSAD,
    EntityIndexFilter,
    EntityIndexHeater,
    EntityIndexHeaterEquip,
    EntityIndexPump,
    EntityIndexRelay,
    EntityIndexSensor,
    EntityIndexValveActuator,
    EntityIndexSchedule,
    EntityIndexGroup,
]

# TypeVar for generic entity classes
EntityIndexTypeVar = TypeVar(
    "EntityIndexTypeVar",
    EntityIndexBackyard,
    EntityIndexBodyOfWater,
    EntityIndexColorLogicLight,
    EntityIndexChlorinator,
    EntityIndexChlorinatorEquip,
    EntityIndexCSAD,
    EntityIndexFilter,
    EntityIndexHeater,
    EntityIndexHeaterEquip,
    EntityIndexPump,
    EntityIndexRelay,
    EntityIndexSensor,
    EntityIndexValveActuator,
)


# Generic entity data class for coordinator storage
# This is used when the specific entity type is not yet known
@dataclass
class EntityIndexData:
    """Generic entity data container used by the coordinator.

    This class stores the raw config and telemetry data before
    it's been associated with a specific entity type.
    """

    msp_config: (
        MSPSchedule
        | MSPBackyard
        | MSPBoW
        | MSPVirtualHeater
        | MSPHeaterEquip
        | MSPRelay
        | MSPFilter
        | MSPSensor
        | MSPColorLogicLight
        | MSPChlorinator
        | MSPChlorinatorEquip
        | MSPCSAD
        | MSPPump
    )
    telemetry: (
        TelemetryBackyard
        | TelemetryBoW
        | TelemetryChlorinator
        | TelemetryColorLogicLight
        | TelemetryFilter
        | TelemetryGroup
        | TelemetryHeater
        | TelemetryPump
        | TelemetryRelay
        | TelemetryValveActuator
        | TelemetryVirtualHeater
        | TelemetryCSAD
        | None
    )


# Type alias for the entity index dictionary
EntityIndexT = dict[int, EntityIndexData]
