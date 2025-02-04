# coding: UTF-8


import xml.etree.ElementTree as ET
import unittest

HTML_DATA = """
<!DOCTYPE html>
<html>
  <head>
    <title>page title</title>
    <style>
      table, th, td {
        border: 1px solid black;
        border-collapse: collapse;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 10px;
        padding-right: 10px;
      }
    </style>
  </head>
  <body>
    <table>
      <tr>
        <th>Start Time</th>
        <th>Export ID</th>
        <th>Duration (hh:mm:ss)</th>
      </tr>
      <tr>
        <td>
          Time 1
        </td>
        <td>
          <a target="_blank" href="status/abc?pretty=1">abc</a>
        </td>
        <td>
          10 seconds
        </td>
      </tr>
    </table>
  </body>
</html>
"""


class TestElementTree(unittest.TestCase):
    def test_fromstring(self):
        root = ET.fromstring(HTML_DATA)
        self.assertEqual(root.tag, "html")
        self.assertEqual(root[0].tag, "head")
        self.assertEqual(root[1].tag, "body")

        body = root.find("body")
        tables = body.findall("table")
        table = tables[0]

        trs = table.findall("tr")
        self.assertEqual(len(trs), 2)
        for tr in trs:
            self.assertEqual(tr.tag, "tr")


if __name__ == "__main__":
    unittest.main()
