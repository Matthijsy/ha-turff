from datetime import timedelta

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

from .const import DOMAIN
from .turff import Turff

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=5)


async def async_setup_entry(hass, entry, async_add_entities):
    config = hass.data[DOMAIN][entry.entry_id]

    session = async_get_clientsession(hass)
    turff = Turff(config[CONF_USERNAME], config[CONF_PASSWORD], session=session)
    sensors = []

    for product in await turff.get_products():
        p = {"id": product["UID"], "name": product["name"]}

        s = TurffProductSensor(p, turff)
        sensors.append(s)

        s = TurffConsumptionSensor(p, turff)
        sensors.append(s)

    async_add_entities(sensors, update_before_add=True)


class TurffProductSensor(Entity):
    """Representation of a Turff Product"""

    def __init__(self, product, turff):
        self._id = product["id"]
        self._product_name = product["name"]
        self._turff = turff
        self._state = None
        self._attrs = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._product_name

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._id

    @property
    def device_state_attributes(self):
        return self._attrs

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:beer"

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        balance = await self._turff.get_product_balance(self._id)

        self._state = sum(balance.values())
        self._attrs = balance

class TurffConsumptionSensor(Entity):
    """Representation of a Turff User consumption"""

    def __init__(self, product, turff):
        self._id = product["id"]
        self._product_name = product["name"]
        self._turff = turff
        self._state = None
        self._attrs = {}

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._product_name + " Consumption"

    @property
    def unique_id(self):
        """Return the unique ID of the sensor."""
        return self._id + "_consumption"

    @property
    def device_state_attributes(self):
        return self._attrs

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:beer"

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        consumption = await self._turff.get_consumption_history(self._id)

        self._state = 0
        self._attrs = {'users': consumption}