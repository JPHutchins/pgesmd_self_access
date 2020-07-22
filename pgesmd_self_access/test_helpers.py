"""Test the functions and methods in pgesmd.helpers."""

import unittest
import os
import time
import json

from .helpers import get_auth_file, get_bulk_id_from_xml, parse_espi_data

PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

answers = [
    (1570086000, 3600, 1067),
    (1570089600, 3600, 917),
    (1570093200, 3600, 912),
    (1570096800, 3600, 759),
    (1570100400, 3600, 594),
    (1570104000, 3600, 650),
    (1570107600, 3600, 677),
    (1570111200, 3600, 760),
    (1570114800, 3600, 696),
    (1570118400, 3600, 854),
    (1570122000, 3600, 1230),
    (1570125600, 3600, 871),
    (1570129200, 3600, 827),
    (1570132800, 3600, 1043),
    (1570136400, 3600, 1234),
    (1570140000, 3600, 1116),
    (1570143600, 3600, 1331),
    (1570147200, 3600, 3363),
    (1570150800, 3600, 4870),
    (1570154400, 3600, 5534),
    (1570158000, 3600, 5542),
    (1570161600, 3600, 6296),
    (1570165200, 3600, 5372),
    (1570168800, 3600, 4148),
]


class TestHelpers(unittest.TestCase):
    """Test pgesmd.helpers."""

    def test_get_auth_file(self):
        """Test get_auth_file()."""
        self.assertEqual(get_auth_file("bad_path"), None)
        self.assertEqual(get_auth_file(f"{PROJECT_PATH}/tests/auth/bad.json"), None)
        self.assertEqual(
            get_auth_file(f"{PROJECT_PATH}/tests/auth/auth.json"),
            (
                "55555",
                "fake_client_id",
                "fake_client_secret",
                "/home/jp/pgesmd/tests/cert/cert.crt",
                "/home/jp/pgesmd/tests/cert/private.key",
            ),
        )

    def test_get_bulk_id(self):
        """Test the Bulk ID parse."""
        xml_fp = open(f"{PROJECT_PATH}/tests/data/espi/espi_1_day.xml", "r")
        xml = xml_fp.read()
        xml_fp.close()

        self.assertEqual(get_bulk_id_from_xml(xml), 50916)

    def test_parse_espi(self):
        """Test parse_espi_data()."""
        xml_fp = open(f"{PROJECT_PATH}/tests/data/espi/espi_1_day.xml", "r")
        xml = xml_fp.read()
        for entry, answer in zip(parse_espi_data(xml), answers):
            self.assertEqual(entry, answer)
        xml_fp.close()

        xml_fp = open(f"{PROJECT_PATH}/tests/data/espi/espi_2_years.xml", "r")
        xml = xml_fp.read()
        dump = []
        for entry in parse_espi_data(xml):
            dump.append(entry)
        xml_fp.close()
        #  17,496 hours / 24 = 729 days of data
        self.assertEqual(len(dump), 17496)

        #  check first and last data points, see actual XML file
        self.assertEqual(dump[0], (1508396400, 3600, 447))
        self.assertEqual(dump[17495], (1571378400, 3600, 1643))


if __name__ == "__main__":
    unittest.main()
