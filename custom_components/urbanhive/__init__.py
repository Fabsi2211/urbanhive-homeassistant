"""Urbanhive Homefarm integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import UrbanhiveCoordinator

# Domain der Integration.
DOMAIN = "urbanhive"

# Die Integration stellt Sensoren und Switches bereit.
PLATFORMS = [
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup(
    hass: HomeAssistant,
    config: dict,
) -> bool:
    """Set up the Urbanhive integration."""

    # Bei einer Config-Entry-Integration
    # wird hier nichts weiter benötigt.
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Urbanhive from a config entry."""

    # Coordinator mit der in Home Assistant
    # hinterlegten IP-Adresse erzeugen.
    coordinator = UrbanhiveCoordinator(
        hass,
        entry.data["ip"],
    )

    # Ersten Abruf durchführen.
    #
    # Home Assistant wartet hier auf die erste
    # erfolgreiche Antwort der Homefarm.
    await coordinator.async_config_entry_first_refresh()

    # Coordinator zentral speichern.
    #
    # Sensor.py und switch.py verwenden später
    # genau denselben Coordinator.
    hass.data.setdefault(
        DOMAIN,
        {},
    )[entry.entry_id] = coordinator

    # Sensoren und Switches laden.
    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload an Urbanhive config entry."""

    # Sensoren und Switches entladen.
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    # Coordinator entfernen.
    if unload_ok:
        hass.data[DOMAIN].pop(
            entry.entry_id,
            None,
        )

    return unload_ok
