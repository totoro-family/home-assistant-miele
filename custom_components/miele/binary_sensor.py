import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import Entity

from custom_components.miele import DATA_DEVICES
from custom_components.miele import DOMAIN as MIELE_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from typing import Callable
from custom_components.miele.device_template import Device

PLATFORMS = ["miele"]

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []


def _map_key(key: str) -> str:
    if key == "signalInfo":
        return "Info"
    elif key == "signalFailure":
        return "Failure"
    elif key == "signalDoor":
        return "Door"


# pylint: disable=W0612
def setup_platform(hass: HomeAssistant, config: ConfigType, add_devices: Callable, discovery_info=None) -> None:
    global ALL_DEVICES

    devices: dict[str, Device] = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_state = device["state"]

        binary_devices = []
        if "signalInfo" in device_state:
            binary_devices.append(MieleBinarySensor(hass, device, "signalInfo"))
        if "signalFailure" in device_state:
            binary_devices.append(MieleBinarySensor(hass, device, "signalFailure"))
        if "signalDoor" in device_state:
            binary_devices.append(MieleBinarySensor(hass, device, "signalDoor"))

        add_devices(binary_devices)
        ALL_DEVICES = ALL_DEVICES + binary_devices


def update_device_state() -> None:
    for device in ALL_DEVICES:
        try:
            device.async_schedule_update_ha_state(True)
        except (AssertionError, AttributeError):
            _LOGGER.debug(
                "Component most likely is disabled manually, if not please report to developer"
                "{}".format(device.entity_id)
            )


class MieleBinarySensor(BinarySensorEntity):
    def __init__(self, hass: HomeAssistant, device: Device, key: str) -> None:
        self._hass = hass
        self._device = device
        self._key = key
        self._ha_key = _map_key(key)

    @property
    def device_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self._device["ident"]["deviceIdentLabel"]["fabNumber"]

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        return self.device_id + "_" + self._ha_key

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        ident = self._device["ident"]

        result = ident["deviceName"]
        if len(result) == 0:
            return ident["type"]["value_localized"] + " " + self._ha_key
        else:
            return result + " " + self._ha_key

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return bool(self._device["state"][self._key])

    @property
    def device_class(self) -> str:
        if self._key == "signalDoor":
            return "door"
        else:
            return "problem"

    async def async_update(self) -> None:
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug("Miele device not found: {}".format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]
