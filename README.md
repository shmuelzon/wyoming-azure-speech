# Wyoming Azure Speech

This project implements a Wyoming protocol server backed by Microsoft Azure's AI
Speech services for speech-to-text transcription and text-to-speech
synthesization.

It includes both a Python package and a pre-built Docker image for simpler
integration.

## Prerequisites

In order to use the Azure AI Speech Service, one must sign up for a (free)
account on Azure at https://portal.azure.com/. As of the writing of this
document, the free tier offers 5 hours for speech-to-text conversion per month
and 0.5 million characters of text-to-speech. Only when those are exceeded, you
will be billed. For more information, check out the Speech Services
[pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/#resources).

Before running the Wyoming server, you need to provide it with the Azure region
serving the Speech Service as well as a subscription key. Those can be generated
by performing the following:
- Create an account at [Azure](https://portal.azure.com)
- Add a new [subscription](https://portal.azure.com/#view/Microsoft_Azure_Billing/SubscriptionsBladeV2)
- Create a new [Speech service](https://portal.azure.com/#view/Microsoft_Azure_ProjectOxford/CognitiveServicesHub/~/SpeechServices)
  - Create a new resource group
  - Choose the region closest to you
  - Choose the "Free F0" pricing tier
- Make a note of one of the generated keys and the region name for later

## Installation

### Running the server

#### Manual

Install and the package:
```bash
pip install wyoming-azure-speech
wyoming-azure-speech --key <KEY> --region <REGION>
```

#### Docker

Pull image and run:
```bash
docker run ghcr.io/shmuelzon/wyoming-azure-speech:latest --key <KEY> --region <REGION>
```

#### Docker Compose

```yaml
services:
  wyoming-azure-speech:
    container_name: wyoming-azure-speech
    image: ghcr.io/shmuelzon/wyoming-azure-speech:latest
    restart: unless-stopped
    pull_policy: always
    environment:
      AZURE_KEY_FILE: /run/secrets/azure_key
      AZURE_REGION_FILE: /run/secrets/azure_region
    secrets:
      - azure_key
      - azure_region

secrets:
  azure_key:
    file: secrets/azure_key.txt
  azure_region:
    file: secrets/azure_region.txt
```

### Add to Home Assistant

You can either click on the image or follow the manual procedure below:

[![Add to Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=wyoming)

- Browse to your Home Assistant instance
- Go to [Settings > Devices & Services](https://my.home-assistant.io/redirect/integrations)
- In the bottom right corner, select the [+ Add Integration button](https://my.home-assistant.io/redirect/config_flow_start?domain=wyoming)
- From the list, select **Wyoming Protocol**.
- Enter the IP and port that the Wyoming server is listening on

## Configuration

The server allows the following configuration options:
| Name | Description | Default Value | Optional environment variable |
| --- | --- | :-: | --- |
| `key` | Azure subscription key | | `AZURE_KEY` or `AZURE_KEY_FILE` to read it from a file |
| `region` | Azure region name | | `AZURE_REGION` or `AZURE_REGION_FILE` to read it from a file |
| `uri` | A URI the server will listen on | `tcp://0.0.0.0:10300` | |
| `transcription-language` | Default language for transcription | `en-US` | |
| `voice` | Default voice for synthesizing | `en-US-AvaMultilingualNeural` | |
| `debug` | Enable debug logs | `False` | |
| `log-format` | The format used for printing log messages | `%(asctime)s:%(levelname)s:%(name)s:%(message)s` | |
