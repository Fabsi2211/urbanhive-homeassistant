"""Sensor entities for Urbanhive."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from . import DOMAIN


async def async_setup_entry(
    hass,
    entry,
    async_add_entities,
):
    """Set up Urbanhive sensors."""

    coordinator = hass.data[
        DOMAIN
    ][entry.entry_id]

    entities = [

        # Temperatur
        UrbanhiveSensor(
            coordinator,
            "temperature",
            "Temperatur",
            UnitOfTemperature.CELSIUS,
            lambda data:
                data[
                    "details"
                ].get(
                    "temperature"
                ),
        ),

        # Luftfeuchtigkeit
        UrbanhiveSensor(
            coordinator,
            "humidity",
            "Luftfeuchtigkeit",
            PERCENTAGE,
            lambda data:
                data[
                    "details"
                ].get(
                    "humidity"
                ),
        ),

        # WLAN-Signal
        UrbanhiveSensor(
            coordinator,
            "signal",
            "Signalstärke",
            SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            lambda data:
                data[
                    "details"
                ].get(
                    "signalStrength"
                ),
        ),

        # Helligkeit
        UrbanhiveSensor(
            coordinator,
            "brightness",
            "Helligkeit",
            PERCENTAGE,
            lambda data:
                data[
                    "details"
                ].get(
                    "brightness"
                ),
        ),
    ]

    # Wasserstand jeder Reihe.
    for index in range(
        len(
            coordinator.data.get(
                "rows",
                [],
            )
        )
    ):

        entities.append(
            UrbanhiveSensor(
                coordinator,
                (
                    f"row_{index + 1}"
                    "_water"
                ),
                (
                    f"Reihe {index + 1}"
                    " Wasserstand"
                ),
                PERCENTAGE,
                lambda data,
                i=index:
                    data[
                        "rows"
                    ][i].get(
                        "waterLevel"
                    ),
            )
        )

    async_add_entities(
        entities
    )


class UrbanhiveSensor(
    CoordinatorEntity,
    SensorEntity,
):
    """Representation of an Urbanhive sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        key,
        name,
        unit,
        value_fn,
    ) -> None:
        """Initialize the sensor."""

        super().__init__(
            coordinator
        )

        self._value_fn = (
            value_fn
        )

        self._attr_name = name

        self._attr_unique_id = (
            f"urbanhive_{key}"
        )

        self._attr_native_unit_of_measurement = (
            unit
        )

    @property
    def native_value(self):
        """Return current sensor value."""

        try:

            return self._value_fn(
                self.coordinator.data
            )

        except (
            KeyError,
            IndexError,
            TypeError,
        ):

            return None
