"""Data coordinator for the Urbanhive Homefarm."""

import asyncio
import logging
from copy import deepcopy
from datetime import timedelta

import aiohttp

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

# Alle 5 Sekunden wird der tatsächliche Zustand
# der Homefarm abgefragt.
UPDATE_INTERVAL = timedelta(
    seconds=5
)

# Maximale Dauer eines HTTP-Requests.
REQUEST_TIMEOUT = 3

# Kurzes Sammelfenster für schnelle Tastendrücke.
#
# Beispiel:
#
# Reihe 1 EIN
# Reihe 2 EIN
# Reihe 3 AUS
#
# innerhalb von 150 ms
# ->
# ein gemeinsamer PUT.
COMMAND_DELAY = 0.15


class UrbanhiveCoordinator(
    DataUpdateCoordinator,
):
    """Coordinate all Urbanhive data."""

    def __init__(
        self,
        hass,
        ip: str,
    ) -> None:
        """Initialize the coordinator."""

        self.ip = ip

        # Basis-URL der Homefarm.
        self.base_url = (
            f"http://{ip}"
        )

        # Verhindert parallele PUT Requests.
        self._command_lock = (
            asyncio.Lock()
        )

        # Wartende Lichtbefehle.
        #
        # Beispiel:
        #
        # {
        #     0: True,
        #     1: False
        # }
        self._pending_commands = {}

        # Aktueller Versand-Task.
        self._command_task = None

        super().__init__(
            hass,
            _LOGGER,
            name="Urbanhive Homefarm",
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self):
        """Fetch current data from the Homefarm."""

        url = (
            f"{self.base_url}"
            "/farm-info"
        )

        timeout = aiohttp.ClientTimeout(
            total=REQUEST_TIMEOUT
        )

        try:

            # HTTP-Session erzeugen.
            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:

                # Farm-Info abrufen.
                async with session.get(
                    url
                ) as response:

                    # HTTP-Fehler erkennen.
                    response.raise_for_status()

                    # JSON auslesen.
                    data = await response.json(
                        content_type=None
                    )

                    # Grundlegende Prüfung.
                    if (
                        not isinstance(
                            data,
                            dict,
                        )
                        or "rows" not in data
                    ):
                        raise UpdateFailed(
                            "Invalid response from Urbanhive"
                        )

                    return data

        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
        ) as err:

            _LOGGER.warning(
                "Could not contact Urbanhive: %s",
                err,
            )

            raise UpdateFailed(
                f"Could not contact Urbanhive: {err}"
            ) from err

    async def async_set_row_light(
        self,
        row_index: int,
        state: bool,
    ) -> None:
        """Queue a row light command."""

        # Den neuen Zustand sofort lokal setzen.
        #
        # Dadurch reagiert die HA-Oberfläche
        # unmittelbar auf den Tastendruck.
        if self.data:

            rows = self.data.get(
                "rows",
                [],
            )

            if row_index < len(rows):

                rows[row_index][
                    "lightOn"
                ] = state

                self.async_set_updated_data(
                    self.data
                )

        # Befehl zwischenspeichern.
        self._pending_commands[
            row_index
        ] = state

        # Falls noch kein Versand läuft,
        # einen neuen Versand starten.
        if (
            self._command_task is None
            or self._command_task.done()
        ):

            self._command_task = (
                self.hass.async_create_task(
                    self._process_commands()
                )
            )

    async def _process_commands(
        self,
    ) -> None:
        """Send queued light commands."""

        # Kurzes Sammelfenster.
        await asyncio.sleep(
            COMMAND_DELAY
        )

        # Verhindert parallele PUT Requests.
        async with self._command_lock:

            # Aktuelle Befehle übernehmen.
            commands = dict(
                self._pending_commands
            )

            # Warteschlange leeren.
            self._pending_commands.clear()

            if not commands:
                return

            # Falls keine Daten vorhanden sind,
            # zuerst aktualisieren.
            if not self.data:

                await self.async_request_refresh()

            if not self.data:

                _LOGGER.error(
                    "No Urbanhive data available"
                )

                return

            try:

                details = self.data[
                    "details"
                ]

                # Kopie der Rows erzeugen.
                rows = deepcopy(
                    self.data[
                        "rows"
                    ]
                )

                # Alle schnellen Tastendrücke
                # auf einmal anwenden.
                for (
                    row_index,
                    state,
                ) in commands.items():

                    if (
                        0 <= row_index
                        < len(rows)
                    ):

                        rows[
                            row_index
                        ][
                            "lightOn"
                        ] = state

                # PUT-Payload erstellen.
                payload = {
                    "brightness": details.get(
                        "brightness",
                        100,
                    ),
                    "lightTime": details.get(
                        "lightTime",
                        {},
                    ),
                    "rows": rows,
                }

                url = (
                    f"{self.base_url}"
                    "/farm-settings"
                )

                timeout = aiohttp.ClientTimeout(
                    total=REQUEST_TIMEOUT
                )

                # PUT an die Homefarm.
                async with aiohttp.ClientSession(
                    timeout=timeout
                ) as session:

                    async with session.put(
                        url,
                        json=payload,
                    ) as response:

                        response.raise_for_status()

                _LOGGER.debug(
                    "Urbanhive command successful: %s",
                    commands,
                )

            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as err:

                _LOGGER.error(
                    "Urbanhive command failed: %s",
                    err,
                )

            # Nach dem PUT den echten Zustand
            # von der Homefarm abrufen.
            await self.async_request_refresh()
