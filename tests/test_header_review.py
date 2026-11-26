import unittest
from unittest.mock import patch

from nightecho.header_review import fetch_range


class HeaderReviewTests(unittest.TestCase):
    @patch("nightecho.header_review.urlopen")
    def test_rejects_full_response_without_reading_body(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.status = 200
        response.headers = {"Content-Length": "236725520"}
        with self.assertRaisesRegex(ValueError, "bounded EDF range"):
            fetch_range("https://example.com/file.edf", 0, 255)
        response.read.assert_not_called()

    @patch("nightecho.header_review.urlopen")
    def test_reads_only_exact_verified_range(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.status = 206
        response.headers = {"Content-Length": "256", "Content-Range": "bytes 0-255/10000"}
        response.read.return_value = bytes(256)
        self.assertEqual(fetch_range("https://example.com/file.edf", 0, 255),
                         (bytes(256), 10000))
        self.assertEqual(urlopen.call_args.args[0].get_header("Range"), "bytes=0-255")
        response.read.assert_called_once_with(256)
