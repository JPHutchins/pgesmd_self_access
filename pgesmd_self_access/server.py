"""A server that handles POST from PGE SMD servers."""

from http.server import BaseHTTPRequestHandler, HTTPServer
from xml.etree import cElementTree as ET
import ssl
import logging
import os

from .helpers import parse_espi_data, get_bulk_id_from_xml

_LOGGER = logging.getLogger(__name__)


class PgePostHandler(BaseHTTPRequestHandler):
    """Handle POST from PGE."""

    api = None
    save_file = None
    filename = None
    to_db = None
    update_path = None

    def do_GET(self):
        _LOGGER.debug(f"Received GET from {self.address_string()}")

        if self.path != "/status":
            return

        status = self.api.get_service_status()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(str(status).encode("utf-8"))
    
    def do_POST(self):
        """Download the ESPI XML and save to database."""
        _LOGGER.debug(f"Received POST from {self.address_string()}")

        if self.path == "/test":
            self.send_response(200)
            self.end_headers()
            return
        
        if self.path == "/refresh":
            self.api.request_latest_data()
            self.send_response(200)
            self.end_headers()
            return

        if self.path != self.update_path:
            _LOGGER.debug(f"Unhandled path {self.path}")
            return

        body = self.rfile.read(int(self.headers.get("Content-Length")))
        _LOGGER.debug(body)
        try:
            batch_list = ET.fromstring(body)
        except ET.ParseError as e:
            _LOGGER.error(f"Could not parse message: {body=} {e=}")
            return
        
        resource_uris = []
        for resource_uri in batch_list:
            resource_uri = resource_uri.text
            if not resource_uri[: len(self.api.utility_uri)] == self.api.utility_uri:
                _LOGGER.error(
                    f"POST from {self.address_string} contains: "
                    f"{body}     "
                    f"{resource_uri[:len(self.api.utility_uri)]}"
                    f" != {self.api.utility_uri}"
                )
                continue
            if resource_uri.partition('correlationID=')[2] == '000000000-b':
                _LOGGER.debug(f'Skipping {resource_uri}')
                continue
            resource_uris.append(resource_uri)
        
        if len(resource_uris) == 0:
            _LOGGER.error("No resources to process")
            return

        self.send_response(200)
        self.end_headers()

        for resource_uri in resource_uris:
            xml_data = self.api.get_espi_data(resource_uri)

            if self.save_file:
                save_name = self.save_file(xml_data, filename=self.filename)
                if save_name:
                    _LOGGER.info(f"XML saved at {save_name}")
                else:
                    _LOGGER.error("File not saved.")

            if self.to_db:
                self.to_db(xml_data)

                
class SelfAccessServer:
    """Server class for PGE SMD Self Access API."""

    def __init__(
        self,
        api_instance,
        port=7999,
        save_file=None,
        filename=None,
        to_db=None,
        close_after=False,
        use_ssl=True,
        update_path="/pgesmd",
    ):
        """Initialize and start the server on construction."""
        PgePostHandler.api = api_instance
        PgePostHandler.save_file = save_file
        PgePostHandler.filename = filename
        PgePostHandler.to_db = to_db
        PgePostHandler.update_path = update_path
        server = HTTPServer(("", port), PgePostHandler)

        if use_ssl:
            server.socket = ssl.wrap_socket(
                server.socket,
                certfile=api_instance.cert[0],
                keyfile=api_instance.cert[1],
                server_side=True,
            )

        if close_after:
            server.handle_request()
        else:
            server.serve_forever()
