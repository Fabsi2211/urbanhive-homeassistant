# Urbanhive Homefarm for Home Assistant

Custom Home Assistant integration for the Urbanhive Homefarm.

The integration communicates directly with the Homefarm through its local REST API.

## Features

- Local REST API
- Temperature
- Humidity
- Wi-Fi signal strength
- Brightness
- Water level for each row
- Individual row light switches
- Fast local switch feedback
- Multiple rapid switch commands are combined
- Automatic synchronization every 5 seconds
- No cloud credentials required

## Installation with HACS

### Custom repository

Until this integration is available in the official HACS repository, add the GitHub repository as a custom repository.

In Home Assistant:

**HACS → Integrations → ⋮ → Custom repositories**

Enter the GitHub repository URL and select:

**Integration**

Then install **Urbanhive Homefarm**.

Restart Home Assistant afterwards.

## Configuration

Go to:

**Settings → Devices & services → Add integration**

Search for:

**Urbanhive Homefarm**

Enter the local IP address of your Homefarm.

The integration is now configured through the Home Assistant UI.

## Local API

The integration uses:

    GET /farm-info

to read the current state.

For light changes it uses:

    PUT /farm-settings

The implementation is based on the REST API documentation supplied by Urbanhive.

## Privacy

The integration communicates directly with the local IP address of the Homefarm.

No Urbanhive cloud credentials are required.

## License

MIT
