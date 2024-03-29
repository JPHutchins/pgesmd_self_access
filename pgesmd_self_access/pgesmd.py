"""Trial config flow for the PGE SMD API library."""

import os
import sys
import logging

from .api import SelfAccessApi
from .server import SelfAccessServer
from .helpers import save_espi_xml, parse_espi_data

_LOGGER = logging.getLogger(__name__)

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Enter your Third Party ID as listed in the Share My Data portal.
THIRD_PARTY_ID = "50916"

# Update the files referenced below with your credentials.
CERT_PATH = f"{PROJECT_PATH}/cert/cert.crt"
KEY_PATH = f"{PROJECT_PATH}/cert/private.key"
AUTH_PATH = f"{PROJECT_PATH}/auth/auth.json"

# Port forwarding.  Forward external port 443 to this application:PORT.
PORT = 7999

# EmonCMS connection info.  https://github.com/emoncms
EMONCMS_IP = "http://192.168.0.40:8080"
EMONCMS_WRITE_KEY = "db4da6f33f8739ea50b0038d2fc96cec"
EMONCMS_NODE = 30

TOKEN_URI = "https://api.pge.com/datacustodian/oauth/v2/token"
UTILITY_URI = "https://api.pge.com"
API_URI = "/GreenButtonConnect/espi"
BULK_RESOURCE_URI = f"{UTILITY_URI}{API_URI}/1_1/resource/Batch/Bulk/{THIRD_PARTY_ID}"


def download_day_data(date):
    """Use to pull particular XML for testing purposes."""

    api = SelfAccessApi.auth()

    if api.request_date_data(date):
        SelfAccessServer(
            api, save_file=save_espi_xml, filename=date, to_db=False, close_after=True
        )


if __name__ == "__main__":
    api = SelfAccessApi.auth()
    request_post = api.request_latest_data()

    try:
        server = SelfAccessServer(api, save_file=save_espi_xml)
    except KeyboardInterrupt:
        pass
