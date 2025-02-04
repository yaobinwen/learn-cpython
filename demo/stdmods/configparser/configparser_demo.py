# coding: UTF-8

"""
This file contains example of using configparser. For its documentation,
see https://docs.python.org/3/library/configparser.html
This document is referred to as `DOC` in the code.
"""

import configparser
import unittest

TEST_CONFIG = """
[Address]
Address=addr1

[Address]
Address=addr2

[Network]
Address=addr3
Address=addr4
"""


class TestConfigParser(unittest.TestCase):
    def test_read_string(self):
        c = configparser.ConfigParser(strict=False)
        c.read_string(TEST_CONFIG)

        self.assertEqual(c["Address"]["Address"], "addr2")
        self.assertEqual(c["Network"]["Address"], "addr4")


if __name__ == "__main__":
    unittest.main()
