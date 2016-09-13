#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import os
import sys
import time
import logging.config
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from urllib2 import URLError, HTTPError

try:
    import mock
    import google_translate
except ImportError as error:
    print error
    sys.exit(1)

# Set up global test settings
from tests import *

class TestSplitText(unittest.TestCase):

    def test_split_text_invalid_text(self):
        split_text_gen = google_translate.utils.split_text(1234, 25)
        self.assertRaises(AssertionError, next, split_text_gen)

    def test_split_text_invalid_maxchunk(self):
        split_text_gen = google_translate.utils.split_text("Text", -1)
        self.assertRaises(AssertionError, next, split_text_gen)

        split_text_gen = google_translate.utils.split_text("Text", 0)
        self.assertRaises(AssertionError, next, split_text_gen)

    def test_split_text_empty_text(self):
        split_text_gen = google_translate.utils.split_text("", 25)
        self.assertRaises(StopIteration, next, split_text_gen)

    def test_split_text_length_smaller_than_maxchunk(self):
        split_text_gen = google_translate.utils.split_text("Some text", 2000)
        self.assertEqual(next(split_text_gen), "Some text")

    def test_split_text_length_greater_than_maxchunk(self):
        text = "This is the first line.\nThis is the second line."
        split_text_gen = google_translate.utils.split_text(text, 30)

        self.assertEqual(next(split_text_gen), "This is the first line.")
        self.assertEqual(next(split_text_gen), "\nThis is the second line.")

        split_text_gen = google_translate.utils.split_text(text, 20)

        self.assertEqual(next(split_text_gen), "This is the first ")
        self.assertEqual(next(split_text_gen), "line.")
        self.assertEqual(next(split_text_gen), "\nThis is the second ")
        self.assertEqual(next(split_text_gen), "line.")

    def test_split_text_large_text(self):
        text = "This-is-a-very-large-sentence-with-no-punctuations"
        split_text_gen = google_translate.utils.split_text(text, 30)
        self.assertRaises(Exception, next, split_text_gen)

    def test_split_text_quoted_text(self):
        punctuations = [google_translate.utils.quote_unicode(char) for char in google_translate.utils.PUNCTUATIONS]
        text = google_translate.utils.quote_unicode("This is the first line.\nThis is the second line.")

        split_text_gen = google_translate.utils.split_text(text, 30, punctuations)

        self.assertEqual(next(split_text_gen), "This%20is%20the%20first%20")
        self.assertEqual(next(split_text_gen), "line.")
        self.assertEqual(next(split_text_gen), "%0AThis%20is%20the%20second%20")
        self.assertEqual(next(split_text_gen), "line.")


class TestFunctions(unittest.TestCase):

    def test_quote_unicode(self):
        ret_value = google_translate.utils.quote_unicode("test test")
        self.assertIsInstance(ret_value, unicode)
        self.assertEqual(ret_value, "test%20test")

        ret_value = google_translate.utils.quote_unicode("τεστ τεστ")
        self.assertIsInstance(ret_value, unicode)
        self.assertEqual(ret_value, "%CF%84%CE%B5%CF%83%CF%84%20%CF%84%CE%B5%CF%83%CF%84")

        self.assertRaises(UnicodeEncodeError, google_translate.utils.quote_unicode, "τεστ τεστ", "ascii")

    def test_unquote_unicode(self):
        ret_value = google_translate.utils.unquote_unicode("test%20test")
        self.assertIsInstance(ret_value, unicode)
        self.assertEqual(ret_value, "test test")

        ret_value = google_translate.utils.unquote_unicode("%CF%84%CE%B5%CF%83%CF%84%20%CF%84%CE%B5%CF%83%CF%84")
        self.assertIsInstance(ret_value, unicode)
        self.assertEqual(ret_value, "τεστ τεστ")

        self.assertRaises(UnicodeEncodeError, google_translate.utils.unquote_unicode, "τεστ%20τεστ", "ascii")

    @mock.patch("google_translate.utils.locale.getpreferredencoding")
    def test_decode_string(self, mock_encoding):
        mock_encoding.return_value = "utf-8"

        # Test with unicode string
        ret_value = google_translate.utils.decode_string("test")
        self.assertIsInstance(ret_value, unicode)
        self.assertEqual(ret_value, "test")

        # Test non unicode string encoding set
        ret_value = google_translate.utils.decode_string("test".encode("latin-1"), "latin-1")
        self.assertIsInstance(ret_value, unicode)
        self.assertEqual(ret_value, "test")

        # Test non unicode string encoding not set
        ret_value = google_translate.utils.decode_string("test".encode("utf-8"))
        self.assertIsInstance(ret_value, unicode)
        self.assertEqual(ret_value, "test")
        mock_encoding.assert_called_once()

    @mock.patch("google_translate.utils.decode_string")
    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.os.path.exists")
    def test_load_from_file(self, mock_path_exists, mock_open, mock_decode_string):
        # Test with invalid filename
        self.assertEqual(google_translate.utils.load_from_file(123456), [])

        # Test with valid filename not exists
        mock_path_exists.return_value = False
        self.assertEqual(google_translate.utils.load_from_file("somefile"), [])
        mock_path_exists.assert_called_once_with("somefile")

        mock_path_exists.reset_mock()

        # Test with valid filename exists
        mock_decode_string.side_effect = lambda x: x
        mock_path_exists.return_value = True
        mock_open.return_value.__enter__.return_value.__iter__.return_value = ["#line1\n", "line2\n", "line3\n"]

        self.assertEqual(google_translate.utils.load_from_file("somefile"), ["line2", "line3"])
        mock_path_exists.assert_called_once_with("somefile")
        mock_open.assert_called_once_with("somefile", "r")
        mock_decode_string.assert_has_calls([mock.call("line2"), mock.call("line3")], any_order=True)

    @mock.patch("google_translate.utils.GzipFile")
    @mock.patch("google_translate.utils.StringIO")
    def test_ungzip_stream(self, mock_stringio, mock_gzipfile):
        # Test IOError raise
        mock_gzipfile.return_value.read.side_effect = IOError("invalid format")
        self.assertEqual(google_translate.utils.ungzip_stream("data"), "data")

        mock_stringio.reset_mock()
        mock_gzipfile.reset_mock()

        # Test not IOError raise
        mock_gzipfile.return_value.read.side_effect = None
        self.assertEqual(google_translate.utils.ungzip_stream("data"), mock_gzipfile.return_value.read.return_value)

        mock_stringio.assert_called_once_with("data")
        mock_gzipfile.assert_called_once_with(fileobj=mock_stringio.return_value)
        mock_gzipfile.return_value.read.assert_called_once()

    @mock.patch("google_translate.utils.urllib2.ProxyHandler")
    @mock.patch("google_translate.utils.urllib2.build_opener")
    def test_make_request(self, mock_build_opener, mock_proxy_handler):
        test_url = "someurl"
        test_proxy = "someproxy"
        test_headers = "someheaders"

        # Test no proxy
        self.assertEqual(google_translate.utils.make_request(test_url), mock_build_opener.return_value.open.return_value)
        mock_proxy_handler.assert_not_called()
        mock_build_opener.assert_called_once()
        mock_build_opener.return_value.open.assert_called_once_with(test_url, timeout=10.0)
        mock_build_opener.return_value.close.assert_called_once()

        mock_build_opener.reset_mock()

        # Test with proxy
        self.assertEqual(google_translate.utils.make_request(test_url, proxy=test_proxy, timeout=5), mock_build_opener.return_value.open.return_value)
        mock_proxy_handler.assert_called_once_with({"http": test_proxy, "https": test_proxy})
        mock_build_opener.assert_called_once_with(mock_proxy_handler.return_value)
        mock_build_opener.return_value.open.assert_called_once_with(test_url, timeout=5)
        mock_build_opener.return_value.close.assert_called_once()

        mock_proxy_handler.reset_mock()
        mock_build_opener.reset_mock()

        # Test add extra headers
        self.assertEqual(google_translate.utils.make_request(test_url, test_headers), mock_build_opener.return_value.open.return_value)
        mock_proxy_handler.assert_not_called()
        mock_build_opener.assert_called_once()
        mock_build_opener.return_value.open.assert_called_once_with(test_url, timeout=10.0)
        mock_build_opener.return_value.close.assert_called_once()
        self.assertEqual(mock_build_opener.return_value.addheaders, test_headers)

        mock_build_opener.reset_mock()

        # Test URLError raise
        mock_build_opener.return_value.open.side_effect = URLError("invalid url")

        self.assertRaises(URLError, google_translate.utils.make_request, test_url)
        mock_proxy_handler.assert_not_called()
        mock_build_opener.assert_called_once()
        mock_build_opener.return_value.open.assert_called_once_with(test_url, timeout=10.0)
        mock_build_opener.return_value.close.assert_called_once()

        mock_build_opener.reset_mock()

        # Test simulation mode
        self.assertIsNone(google_translate.utils.make_request(test_url, simulate=True))
        mock_proxy_handler.assert_not_called()
        mock_build_opener.assert_not_called()

    @mock.patch("google_translate.utils.decode_string")
    @mock.patch("google_translate.utils.ungzip_stream")
    def test_parse_reply(self, mock_ungzip, mock_decode_string):
        mock_reply = mock.MagicMock(spec=file)

        # Test no error raise
        self.assertEqual(google_translate.utils.parse_reply(mock_reply), mock_decode_string.return_value)

        mock_reply.read.assert_called_once()
        mock_ungzip.assert_called_once_with(mock_reply.read.return_value)
        mock_reply.close.assert_called_once()
        mock_decode_string.assert_called_once_with(mock_ungzip.return_value, "UTF-8")

        mock_decode_string.reset_mock()

        # Test user specified encoding
        self.assertEqual(google_translate.utils.parse_reply(mock_reply, "ascii"), mock_decode_string.return_value)
        mock_decode_string.assert_called_once_with(mock_ungzip.return_value, "ascii")

        # Test Attribute error raised
        mock_reply.read.side_effect = AttributeError("invalid attribute 'read'")
        self.assertRaises(AttributeError, google_translate.utils.parse_reply, mock_reply)

    @mock.patch("google_translate.utils.os.path")
    def test_get_absolute_path(self, mock_os_path):
        self.assertEqual(google_translate.utils.get_absolute_path("test"), mock_os_path.dirname.return_value)
        mock_os_path.abspath.assert_called_once_with("test")
        mock_os_path.dirname.assert_called_once_with(mock_os_path.abspath.return_value)

    def test_display_unicode_item(self):
        self.assertEqual(google_translate.utils.display_unicode_item(["σπίτι", "μολύβι"]), "['σπίτι', 'μολύβι']")
        self.assertEqual(google_translate.utils.display_unicode_item(["house", "pencil"]), "['house', 'pencil']")
        self.assertEqual(google_translate.utils.display_unicode_item({"key": "τιμή"}), "{'key': 'τιμή'}")

    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.json.dump")
    @mock.patch("google_translate.utils.os.path.dirname")
    def test_write_dict_success_no_dirname(self, mock_dirname, mock_jdump, mock_open):
        mock_dirname.return_value = ""

        self.assertTrue(google_translate.utils.write_dict("file", {"a": 5}))
        mock_dirname.assert_called_once_with("file")
        mock_open.assert_called_once_with("file", "w")
        mock_jdump.assert_called_once_with([("a", 5)], mock_open.return_value.__enter__.return_value)

    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.json.dump")
    @mock.patch("google_translate.utils.os.path.isdir")
    @mock.patch("google_translate.utils.os.path.dirname")
    def test_write_dict_success_path_exists(self, mock_dirname, mock_isdir, mock_jdump, mock_open):
        mock_dirname.return_value = "/home/user/.config"
        mock_isdir.return_value = True

        self.assertTrue(google_translate.utils.write_dict("/home/user/.config/file", {"a": 5}))
        mock_dirname.assert_called_once_with("/home/user/.config/file")
        mock_isdir.assert_called_once_with(mock_dirname.return_value)
        mock_open.assert_called_once_with("/home/user/.config/file", "w")
        mock_jdump.assert_called_once_with([("a", 5)], mock_open.return_value.__enter__.return_value)

    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.json.dump")
    @mock.patch("google_translate.utils.os.path.isdir")
    @mock.patch("google_translate.utils.os.path.dirname")
    @mock.patch("google_translate.utils.os.makedirs")
    def test_write_dict_success_path_not_exists(self, mock_makedirs, mock_dirname, mock_isdir, mock_jdump, mock_open):
        mock_dirname.return_value = "/home/user/downloads"
        mock_isdir.return_value = False

        self.assertTrue(google_translate.utils.write_dict("/home/user/downloads/file", {"a": 5}))
        mock_dirname.assert_called_once_with("/home/user/downloads/file")
        mock_isdir.assert_called_once_with(mock_dirname.return_value)
        mock_makedirs.assert_called_once_with(mock_dirname.return_value)
        mock_open.assert_called_once_with("/home/user/downloads/file", "w")
        mock_jdump.assert_called_once_with([("a", 5)], mock_open.return_value.__enter__.return_value)

    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.os.path.dirname")
    def test_write_dict_failure_on_open(self, mock_dirname, mock_open):
        mock_dirname.return_value = ""
        mock_open.side_effect = IOError("Permission denied")

        self.assertFalse(google_translate.utils.write_dict("file", {"a": 5}))
        mock_dirname.assert_called_once_with("file")
        mock_open.assert_called_once_with("file", "w")

    @mock.patch("google_translate.utils.os.path.isdir")
    @mock.patch("google_translate.utils.os.path.dirname")
    @mock.patch("google_translate.utils.os.makedirs")
    def test_write_dict_failure_on_makedirs(self, mock_makedirs, mock_dirname, mock_isdir):
        mock_dirname.return_value = "/home/user/downloads"
        mock_isdir.return_value = False
        mock_makedirs.side_effect = OSError("Permission denied")

        self.assertFalse(google_translate.utils.write_dict("/home/user/downloads/file", {"a": 5}))
        mock_dirname.assert_called_once_with("/home/user/downloads/file")
        mock_isdir.assert_called_once_with(mock_dirname.return_value)
        mock_makedirs.assert_called_once_with(mock_dirname.return_value)

    def test_write_dict_invalid_filename(self):
        self.assertRaises(AssertionError, google_translate.utils.write_dict, 1234, {})

    def test_write_dict_invalid_dictionary(self):
        self.assertRaises(AssertionError, google_translate.utils.write_dict, "file", [])

    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.json.load")
    @mock.patch("google_translate.utils.os.path.exists")
    def test_get_dict_success(self, mock_exists, mock_jload, mock_open):
        mock_exists.return_value = True
        mock_jload.return_value = [("a", 5)]

        self.assertEqual(google_translate.utils.get_dict("file"), {"a": 5})
        mock_exists.assert_called_once_with("file")
        mock_open.assert_called_once_with("file", "r")
        mock_jload.assert_called_once_with(mock_open.return_value.__enter__.return_value)

    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.json.load")
    @mock.patch("google_translate.utils.os.path.exists")
    def test_get_dict_failure_invalid_format(self, mock_exists, mock_jload, mock_open):
        mock_exists.return_value = True
        mock_jload.side_effect = ValueError("invalid JSON format")

        self.assertIsNone(google_translate.utils.get_dict("file"))
        mock_exists.assert_called_once_with("file")
        mock_open.assert_called_once_with("file", "r")
        mock_jload.assert_called_once_with(mock_open.return_value.__enter__.return_value)

    @mock.patch("google_translate.utils.open")
    @mock.patch("google_translate.utils.os.path.exists")
    def test_get_dict_failure_permission_denied(self, mock_exists, mock_open):
        mock_exists.return_value = True
        mock_open.return_value.__enter__.side_effect = IOError("Permission denied")

        self.assertIsNone(google_translate.utils.get_dict("file"))
        mock_exists.assert_called_once_with("file")
        mock_open.assert_called_once_with("file", "r")

    @mock.patch("google_translate.utils.os.path.exists")
    def test_get_dict_failure_file_not_exists(self, mock_exists):
        mock_exists.return_value = False

        self.assertIsNone(google_translate.utils.get_dict("file"))
        mock_exists.assert_called_once_with("file")

    def test_get_dict_invalid_filename(self):
        self.assertRaises(AssertionError, google_translate.utils.get_dict, 1234)


def main():
    unittest.main()


if __name__ == '__main__':
    main()
