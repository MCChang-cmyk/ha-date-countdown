"""Countdown sensors."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from .entity import CountdownEntity

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([CountdownSensor(entry, key, index, unit, device_class)
        for key, index, unit, device_class in (
            ("days_remaining", 1, "d", None),
            ("remaining_percentage", 2, "%", None),
            ("due_date", 0, None, SensorDeviceClass.DATE),
        )])

class CountdownSensor(CountdownEntity, SensorEntity):
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, entry, key, index, unit, device_class):
        super().__init__(entry, key)
        self.index = index
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class

    @property
    def native_value(self):
        return self.values[self.index]

    @property
    def extra_state_attributes(self):
        due, remaining, percentage = self.values
        return {**self.settings, "due_date": due.isoformat(),
                "days_remaining": remaining, "remaining_percentage": percentage}
