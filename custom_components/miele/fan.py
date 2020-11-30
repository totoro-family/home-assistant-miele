import logging

from datetime import timedelta

from homeassistant.helpers.entity import Entity
from homeassistant.components.fan import FanEntity, SUPPORT_SET_SPEED

from custom_components.miele import DOMAIN as MIELE_DOMAIN, DATA_CLIENT, DATA_DEVICES

PLATFORMS = ['miele']

_LOGGER = logging.getLogger(__name__)

ALL_DEVICES = []

SUPPORTED_TYPES = [18]


OPERATION_SPEEDS = [0, 1, 2, 3, 4]


# pylint: disable=W0612
def setup_platform(hass, config, add_devices, discovery_info=None):
    global ALL_DEVICES

    devices = hass.data[MIELE_DOMAIN][DATA_DEVICES]
    for k, device in devices.items():
        device_type = device['ident']['type']

        fan_devices = []
        if device_type['value_raw'] in SUPPORTED_TYPES:
            fan_devices.append(MieleFan(hass, device))

        add_devices(fan_devices)
        ALL_DEVICES = ALL_DEVICES + fan_devices


def update_device_state():
    for device in ALL_DEVICES:
        device.async_schedule_update_ha_state(True)


class MieleFan(FanEntity):
    def __init__(self, hass, device):
        self._hass = hass
        self._device = device
        self._ha_key = 'fan'

    @property
    def device_id(self):
        """Return the unique ID for this fan."""
        return self._device['ident']['deviceIdentLabel']['fabNumber']

    @property
    def unique_id(self):
        """Return the unique ID for this fan."""
        return self.device_id

    @property
    def name(self):
        """Return the name of the fan."""
        ident = self._device['ident']

        result = ident['deviceName']
        if len(result) == 0:
            return ident['type']['value_localized']
        else:
            return result

    @property
    def is_on(self):
        """Return the state of the fan."""
        return self._device['state']['status']['value_raw'] != 1

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return OPERATION_SPEEDS

    @property
    def speed(self):
        """Return the current speed"""
        return self._device['state']['ventilationStep']['value_raw']

    async def turn_on(self, speed = None, **kwargs):
        service_parameters = {
            'device_id': self.device_id,
            'body': {'powerOn': True,
                     'ventilationStep': speed}
        }
        self._hass.services.call(MIELE_DOMAIN, 'action', service_parameters)

    async def turn_off(self, **kwargs):
        service_parameters = {
            'device_id': self.device_id,
            'body': {'powerOff': True}
        }
        self._hass.services.call(MIELE_DOMAIN, 'action', service_parameters)

    async def async_set_speed(self, speed):
        service_parameters = {
            'device_id': self.device_id,
            'body': {'ventilationStep': speed}
        }
        self._hass.services.call(MIELE_DOMAIN, 'action', service_parameters)

    async def async_update(self):
        if not self.device_id in self._hass.data[MIELE_DOMAIN][DATA_DEVICES]:
            _LOGGER.debug('Miele device not found: {}'.format(self.device_id))
        else:
            self._device = self._hass.data[MIELE_DOMAIN][DATA_DEVICES][self.device_id]
