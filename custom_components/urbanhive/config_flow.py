"""Config flow for Urbanhive Homefarm."""

import asyncio
import ipaddress

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS

from . import DOMAIN

# Maximale Zeit für den Verbindungstest.
REQUEST_TIMEOUT = 3


async def validate_connection(ip: str) -> None:
    """Check whether the Urbanhive Homefarm is reachable."""

    # Prüfen, ob die eingegebene Adresse tatsächlich
    # eine gültige IPv4- oder IPv6-Adresse ist.
    try:
        ipaddress.ip_address(ip)
    except ValueError as err:
        raise InvalidResponse from err

    # Endpoint der Urbanhive REST API.
    url = f"http://{ip}/farm-info"

    timeout = aiohttp.ClientTimeout(
        total=REQUEST_TIMEOUT
    )

    try:
        # HTTP-Session erzeugen.
        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            # /farm-info abrufen.
            async with session.get(url) as response:

                # HTTP-Status prüfen.
                if response.status != 200:
                    raise CannotConnect

                # JSON auslesen.
                data = await response.json(
                    content_type=None
                )

                # Wir erwarten mindestens "rows".
                if (
                    not isinstance(data, dict)
                    or "rows" not in data
                ):
                    raise InvalidResponse

    except (
        aiohttp.ClientError,
        asyncio.TimeoutError,
    ) as err:
        raise CannotConnect from err


class CannotConnect(Exception):
    """Error when the Homefarm cannot be reached."""


class InvalidResponse(Exception):
    """Error when the Homefarm response is invalid."""


class UrbanhiveConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle an Urbanhive config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input=None,
    ):
        """Handle the initial setup."""

        errors = {}

        if user_input is not None:

            # IP-Adresse aus dem Formular holen.
            ip = user_input[
                CONF_IP_ADDRESS
            ].strip()

            try:

                # Verbindung zur Homefarm testen.
                await validate_connection(ip)

            except CannotConnect:

                # Fehlermeldung im UI.
                errors[
                    "base"
                ] = "cannot_connect"

            except InvalidResponse:

                errors[
                    "base"
                ] = "invalid_response"

            else:

                # IP-Adresse als eindeutige ID verwenden.
                await self.async_set_unique_id(
                    f"urbanhive_{ip}"
                )

                # Verhindert, dass dieselbe Homefarm
                # zweimal eingerichtet wird.
                self._abort_if_unique_id_configured()

                # Config Entry erstellen.
                return self.async_create_entry(
                    title="Urbanhive Homefarm",
                    data={
                        "ip": ip,
                    },
                )

        # Formular anzeigen.
        schema = vol.Schema(
            {
                vol.Required(CONF_IP_ADDRESS,): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
