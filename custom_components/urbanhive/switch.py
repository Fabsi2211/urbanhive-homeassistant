"""Switch entities for Urbanhive."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from . import DOMAIN


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
):
    """Set up Urbanhive row switches."""

    # Gemeinsamen Coordinator holen.
    coordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    entities = []

    # Für jede Reihe einen Switch erzeugen.
    for index in range(
        len(
            coordinator.data.get(
                "rows",
                [],
            )
        )
    ):

        entities.append(
            UrbanhiveRowLightSwitch(
                coordinator,
                index,
            )
        )

    async_add_entities(
        entities
    )


class UrbanhiveRowLightSwitch(
    CoordinatorEntity,
    SwitchEntity,
):
    """Representation of one row light."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        row_index: int,
    ) -> None:
        """Initialize the switch."""

        super().__init__(
            coordinator
        )

        self._row_index = (
            row_index
        )

        row_number = (
            row_index + 1
        )

        self._attr_name = (
            f"Reihe {row_number} Licht"
        )

        # Wichtig:
        # Die Unique IDs entsprechen unseren
        # bisherigen Entity IDs.
        self._attr_unique_id = (
            f"urbanhive_row_"
            f"{row_number}_light"
        )

    @property
    def is_on(self):
        """Return current light state."""

        try:

            return bool(
                self.coordinator.data[
                    "rows"
                ][
                    self._row_index
                ][
                    "lightOn"
                ]
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ):

            return None

    async def async_turn_on(
        self,
        **kwargs,
    ):
        """Turn light on."""

        await (
            self.coordinator
            .async_set_row_light(
                self._row_index,
                True,
            )
        )

    async def async_turn_off(
        self,
        **kwargs,
    ):
        """Turn light off."""

        await (
            self.coordinator
            .async_set_row_light(
                self._row_index,
                False,
            )
        )
