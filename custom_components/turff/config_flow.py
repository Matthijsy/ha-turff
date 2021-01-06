from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from .const import DOMAIN
from .turff import Turff

AUTH_SCHEMA = vol.Schema(
    {vol.Required(CONF_USERNAME): cv.string, vol.Required(CONF_PASSWORD): cv.string}
)


class TurffConfigFLow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """ Ask for username and password """
        if user_input is not None:
            return await self._async_create(user_input)

        return self.async_show_form(step_id="user", data_schema=AUTH_SCHEMA)

    async def _async_create(self, user_input):
        """ Get the House name and create the entity"""
        session = async_get_clientsession(self.hass)
        turff = Turff(
            user_input[CONF_USERNAME], user_input[CONF_PASSWORD], session=session
        )
        if not await turff.validate_credentials():
            return self.async_show_form(
                step_id="user",
                data_schema=AUTH_SCHEMA,
                errors={"base": "invalid_credentials"},
            )

        house_name = await turff.get_house_name()
        return self.async_create_entry(title=house_name, data=user_input)
