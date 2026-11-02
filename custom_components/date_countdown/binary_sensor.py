"""Replacement status."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .entity import CountdownEntity

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([DueSensor(entry)])

class DueSensor(CountdownEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, entry):
        super().__init__(entry, "due")

    @property
    def is_on(self):
        return self.values[1] <= 0
