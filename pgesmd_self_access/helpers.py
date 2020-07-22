"""Helper functinos for pgesmd."""

import json
import os
import requests
import logging
import time
from datetime import datetime
from operator import itemgetter
from xml.etree import cElementTree as ET
from io import StringIO

_LOGGER = logging.getLogger(__name__)


def get_auth_file(auth_path=f"{os.getcwd()}/auth/auth.json"):
    """Try to open auth.json and return tuple."""
    try:
        with open(auth_path) as auth:
            data = auth.read()
            json_data = json.loads(data)
            try:
                third_party_id = json_data["third_party_id"]
                client_id = json_data["client_id"]
                client_secret = json_data["client_secret"]
                cert_crt_path = json_data["cert_crt_path"]
                cert_key_path = json_data["cert_key_path"]
                return (
                    third_party_id,
                    client_id,
                    client_secret,
                    cert_crt_path,
                    cert_key_path,
                )
            except KeyError:
                _LOGGER.error(
                    """
                    Auth file should be JSON:
                    {
                        "third_party_id" : string,
                        "client_id" : string,
                        "client_secret" : string,
                        "cert_crt_path" : string (full path),
                        "cert_key_path" : string (full path)
                    }
                    """
                )
            return None
    except FileNotFoundError:
        _LOGGER.error(f"Auth file not found at {auth_path}.")
        return None


def get_bulk_id_from_xml(
    xml, ns="{http://naesb.org/espi}", ns1="{http://www.w3.org/2005/Atom}"
):
    """Get the PGE Bulk ID from the incoming xml."""
    root = ET.fromstring(xml)
    for child in root.iter(f"{ns1}link"):
        link = child.attrib["href"]
        break
    for i in range(len(link) - 1, 0, -1):
        if link[i] == "/":
            break
    return int(link[i + 1 :])


def parse_espi_data(xml, ns="{http://naesb.org/espi}"):
    """Generate ESPI tuple from ESPI XML.

    Sequentially yields a tuple for each Interval Reading:
        (start, duration, watthours)

    The transition from Daylight Savings Time to Daylight Standard
    Time or inverse are ignored as follows:
    - If the "clocks are set back" then a UTC data point is repeated.  The
        repetition is ignored in order to maintain 24 hours per day.
    - If the "clocks are set forward" then a UTC data point is missing.  The
        missing hour is filled with the average of the previous and following
        values in order to maintain 24 hours per day.
    """
    _LOGGER.debug(f"Parsing the XML.")

    # Find initial values
    root = ET.fromstring(xml)
    for child in root.iter(f"{ns}timePeriod"):
        first_start = int(child.find(f"{ns}start").text)
        duration = int(child.find(f"{ns}duration").text)
        break
    previous = (first_start - duration, 0, 0)
    root.clear()

    xml = StringIO(xml)

    # Find all values
    it = map(itemgetter(1), iter(ET.iterparse(xml)))
    for data in it:
        if data.tag == f"{ns}powerOfTenMultiplier":
            mp = int(data.text)
        if data.tag == f"{ns}IntervalBlock":
            for interval in data.findall(f"{ns}IntervalReading"):
                time_period = interval.find(f"{ns}timePeriod")

                duration = int(time_period.find(f"{ns}duration").text)
                start = int(time_period.find(f"{ns}start").text)
                value = int(interval.find(f"{ns}value").text)
                watt_hours = int(round(value * pow(10, mp) * duration / 3600))

                if start == previous[0]:  # clocks back
                    continue

                if not start == previous[0] + duration:  # clocks forward
                    start = previous[0] + duration
                    watt_hours = int((previous[2] + watt_hours) / 2)
                    previous = (start, duration, watt_hours)
                    yield (start, duration, watt_hours)
                    continue

                previous = (start, duration, watt_hours)
                yield (start, duration, watt_hours)

            data.clear()


def save_espi_xml(self, xml_data, filename=None):
    """Save ESPI XML to a file named by timestamp or filename key."""
    if filename:
        save_name = f"{os.getcwd()}/data/espi_xml/{filename}.xml"
    else:
        timestamp = time.strftime("%y.%m.%d %H:%M:%S", time.localtime())
        save_name = f"{os.getcwd()}/data/espi_xml/{timestamp}.xml"

    with open(save_name, "w") as file:
        file.write(xml_data)
    return save_name


def get_emoncms_from_espi(xml_data, emoncms_node=30):
    """Parse ESPI data for export to emonCMS."""
    root = ET.fromstring(xml_data)
    ns = {"espi": "http://naesb.org/espi"}

    emoncms_data = []

    multiplier = pow(10, int(root.find(".//espi:powerOfTenMultiplier", ns).text))

    date_start = int(root.find(".//espi:interval", ns).find(".//espi:start", ns).text)

    interval_block = root.find(".//espi:IntervalBlock", ns)
    for reading in interval_block.findall(".//espi:IntervalReading", ns):
        start = int(reading.find(".//espi:start", ns).text)
        value = int(reading.find(".//espi:value", ns).text)
        watt_hours = int(value * multiplier)
        offset = start - date_start

        emoncms_data.append([offset, emoncms_node, watt_hours])

    return (date_start, emoncms_data)


def post_data_to_emoncms(for_emoncms, emoncms_ip, emoncms_write_key):
    """Send the bulk data to emonCMS."""
    date_start, emoncms_data = for_emoncms

    params = {
        "apikey": emoncms_write_key,
        "time": date_start,
        "data": str(emoncms_data),
    }

    _LOGGER.debug(f"Sending to emoncms with params: {params}")

    response = requests.post(f"{emoncms_ip}/input/bulk", params=params)

    if response:
        if response.text == "ok":
            _LOGGER.info("Data sent to emonCMS.")
            return True
        _LOGGER.error(f"emonCMS replied with: {response.text}")
        return False
    _LOGGER.error(f"No response from emonCMS at {emoncms_ip}/input/bulk")
    return False
