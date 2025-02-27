"""Support for switches through the SmartThings cloud API."""

from __future__ import annotations

from collections.abc import Sequence
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# from pysmartthings import Capability
from .capability import (
    # ATTRIBUTE_OFF_VALUES,
    # ATTRIBUTE_ON_VALUES,
    # ATTRIBUTES,
    # CAPABILITIES,
    # CAPABILITIES_TO_ATTRIBUTES,
    # Attribute,
    Capability,
)
from .const import DATA_BROKERS, DOMAIN
from .entity import SmartThingsEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add switches for a config entry."""
    broker = hass.data[DOMAIN][DATA_BROKERS][config_entry.entry_id]

    _LOGGER.debug(
        "NB looking for switches",
    )

    #    async_add_entities(
    #        SmartThingsSwitch(device,"main", "switch")
    #        for device in broker.devices.values()
    #        if broker.any_assigned(device.device_id, "switch")
    #    )

    myswitches = []

    for device in broker.devices.values():
        _LOGGER.debug(
            "NB first switch device: %s components: %s",
            device.device_id,
            device.components,
        )
        if broker.any_assigned(device.device_id, "switch"):
            components = device.components
            capabilities = device.capabilities
            _LOGGER.debug(
                "NB about to add_entities switch for device : %s com=%s cap= %s",
                device.device_id,
                components,
                capabilities,
            )
            if "samsungce.lamp" in capabilities:
                _LOGGER.debug(
                    "NB found samsungce.lamp in main section ",
                )
                myswitches.append(SmartThingsSwitch(device, "main", "brightnessLevel"))
            else:
                myswitches.append(SmartThingsSwitch(device, "main", "switch"))

    async_add_entities(myswitches)
    #
    #        if broker.any_assigned(device.device_id, "samsungce.lamp"):
    #            _LOGGER.debug(
    #                  "NB found any_assigned samsungce.lamp ",
    #            )
    #            async_add_entities(SmartThingsSwitch(device,"main", "switch"))

    switches = []
    for device in broker.devices.values():
        for component in device.components:
            if "switch" in device.components[component]:
                switches.append(SmartThingsSwitch(device, component, "switch"))

            capability = device.components[component]

            _LOGGER.debug(
                "NB switch component: %s capability : %s ",
                component,
                capability,
            )

            if "samsungce.lamp" in capability:
                switches.append(SmartThingsSwitch(device, component, "brightnessLevel"))
                _LOGGER.debug(
                    "NB found samsungce.lamp ",
                )

    async_add_entities(switches)


def get_capabilities(capabilities: Sequence[str]) -> Sequence[str] | None:
    """Return all capabilities supported if minimum required are present."""

    _LOGGER.debug(
        "NB switch get_capabilities: %s ",
        capabilities,
    )

    # Must be able to be turned on/off.
    if Capability.switch in capabilities:
        _LOGGER.debug(
            "NB switch found switch in capabilities: %s ",
            capabilities,
        )
        return [Capability.switch, Capability.energy_meter, Capability.power_meter]
    if Capability.oven_light in capabilities:
        _LOGGER.debug(
            "NB switch found oven_light in capabilities: %s ",
            capabilities,
        )
        return [Capability.oven_light]
    return None


class SmartThingsSwitch(SmartThingsEntity, SwitchEntity):
    """Define a SmartThings switch."""

    def __init__(self, device, component, attribute) -> None:
        """Init the class."""
        super().__init__(device)
        self._component = component
        self._attribute = attribute

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        if self._attribute == "brightnessLevel":
            switch_name = "light"
        else:
            switch_name = "switch"

        if self._component == "main":
            return f"{self._device.label} {switch_name}"
        return f"{self._device.label} {self._component} {switch_name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""

        if self._attribute == "brightnessLevel":
            switch_name = "light"
        else:
            switch_name = ""

        if self._component == "main":
            return f"{self._device.device_id}.{switch_name}"
        return f"{self._device.device_id}.{self._component}.{switch_name}"

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""

        if self._attribute == "brightnessLevel":
            _LOGGER.debug(
                "NB switch async_turn_off samsungce.lamp: component = %s attribute: %s ",
                self._component,
                self._attribute,
            )
            #            await self._device.set_brightnesslevel(level="off", set_status=True, component_id=self._component)
            await self._device.command(
                self._component, "samsungce.lamp", "setBrightnessLevel", ["off"]
            )
        else:
            await self._device.switch_off(set_status=True, component_id=self._component)

        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""

        if self._attribute == "brightnessLevel":
            _LOGGER.debug(
                "NB switch async_turn_on samsungce.lamp: component = %s attribute: %s ",
                self._component,
                self._attribute,
            )
            #            await self._device.set_brightnesslevel(level="high", set_status=True, component_id=self._component)
            await self._device.command(
                self._component, "samsungce.lamp", "setBrightnessLevel", ["high"]
            )
        else:
            await self._device.switch_on(set_status=True, component_id=self._component)

        # State is set optimistically in the command above, therefore update
        # the entity state ahead of receiving the confirming push updates
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        _LOGGER.debug(
            "NB switch is_on first: component = %s attrib: %s status: %s",
            self._component,
            self._attribute,
            self._device.status.switch,
        )

        if self._component == "main":
            if self._attribute == "brightnessLevel":
                value = self._device.status.attributes[self._attribute].value

                _LOGGER.debug(
                    "NB switch is_on brightnessLevel value = %s",
                    value,
                )
                if value == "high":
                    return True
                return False
            return self._device.status.switch

        value = (
            self._device.status.components[self._component]
            .attributes[self._attribute]
            .value
        )
        _LOGGER.debug(
            "NB switch is_on second: component = %s status: %s : %s: %s",
            self._component,
            self._device.status.switch,
            self._device.status.components[self._component].switch,
            value,
        )

        if (
            self._device.status.components[self._component]
            .attributes[self._attribute]
            .value
            == "high"
        ):
            return True

        return self._device.status.components[self._component].switch
