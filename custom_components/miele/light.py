import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.components.light import LightEntity
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType
from typing import Callable

from custom_components.miele import DATA_CLIENT, DATA_DEVICES
from custom_components.miele import DOMAIN as MIELE_DOMAIN
from custom_components.miele.device_template import Device

PLATFORMS = ["miele"]

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []

SUPPORTED_TYPES = [17, 18, 32, 33, 34, 68]


# pylint: disable=W0612
def setup_platform(hass:HomeAssistant, config:ConfigType, add_devices:Callable, discovery_info=None) -> None:
    global ALL_DEVICES

    devices = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_type = device["ident"]["type"]

        light_devices = []
        if device_type["value_raw"] in SUPPORTED_TYPES:
            light_devices.append(MieleLight(hass, device))

        add_devices(light_devices)
        ALL_DEVICES = ALL_DEVICES + light_devices


def update_device_state() -> None:
    for device in ALL_DEVICES:
        try:
            device.async_schedule_update_ha_state(True)
        except (AssertionError, AttributeError):
            _LOGGER.debug(
                "Component most likely is disabled manually, if not please report to developer"
                "{}".format(device.entity_id)
            )


class MieleLight(LightEntity):
    def __init__(self, hass:HomeAssistant, device:Device) -> None:
        self._hass = hass
        self._device = device
        self._ha_key = "light"

    @property
    def device_id(self)-> str:
        """Return the unique ID for this light."""
        return self._device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this light."""
        return self.device_id

    @property
    def name(self) -> str:
        """Return the name of the light."""
        ident = self._device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            return ident["type"]["value_localized"]
        else:
            return result

    @property
    def is_on(self) -> bool:
        """Return the state of the light."""
        return self._device["state"]["light"] == 1

    def turn_on(self, **kwargs) -> None:
        service_parameters = {"device_id": self.device_id, "body": {"light": 1}}
        self._hass.services.call(MIELE_DOMAIN, "action", service_parameters)

    def turn_off(self, **kwargs) -> None:
        service_parameters = {"device_id": self.device_id, "body": {"light": 2}}
        self._hass.services.call(MIELE_DOMAIN, "action", service_parameters)

    async def async_update(self) -> None:
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug("Miele device not found: {}".format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]
