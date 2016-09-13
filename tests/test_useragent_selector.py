#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import sys
import random
import os.path
import unittest

from urllib2 import URLError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mock
    from google_translate import UserAgentSelector
except ImportError as error:
    print error
    sys.exit(1)

# Set up global test settings
from tests import *


class TestPrivateMethods(unittest.TestCase):

    def setUp(self):
        self.selector = UserAgentSelector()
        self.ua_list = ["ua-1", "ua-2", "ua-3", "ua-3"]
        self.headers = [("User-Agent", UserAgentSelector.DEFAULT_UA)]

    @mock.patch("google_translate.selectors.make_request")
    @mock.patch("google_translate.selectors.parse_reply", return_value="<textarea var1='1', var2='2'>ua-1\nua-2\nua-3</textarea>")
    def test_get_from_http(self, mock_parse_reply, mock_make_request):
        self.assertEqual(self.selector._get_from_http(), self.ua_list[:3])

        mock_make_request.assert_called_once_with(UserAgentSelector.HTTP_URL, self.headers)
        mock_parse_reply.assert_called_once_with(mock_make_request.return_value)

        mock_parse_reply.reset_mock()
        mock_make_request.reset_mock()

        mock_make_request.side_effect = URLError("invalid url")

        self.assertIsNone(self.selector._get_from_http())

        mock_make_request.assert_called_once_with(UserAgentSelector.HTTP_URL, self.headers)
        mock_parse_reply.assert_not_called()

    def test_append_to_ua_list(self):
        self.selector._append_to_ua_list(None)
        self.assertEqual(self.selector._user_agent_list, [])

        self.selector._append_to_ua_list(self.ua_list)
        self.assertEqual(self.selector._user_agent_list, self.ua_list[:3])

        self.selector._append_to_ua_list(['', "ua-2", "ua-5"])
        self.assertEqual(self.selector._user_agent_list, ["ua-1", "ua-2", "ua-3", "ua-5"])


class TestUserAgentSelector(unittest.TestCase):

    def test_default_ua(self):
        selector = UserAgentSelector()
        self.assertEqual(selector.get_useragent(), UserAgentSelector.DEFAULT_UA)

    def test_user_specified_ua(self):
        selector = UserAgentSelector("testua")
        self.assertEqual(selector.get_useragent(), "testua")

        selector = UserAgentSelector(123456)
        self.assertEqual(selector.get_useragent(), UserAgentSelector.DEFAULT_UA)

        selector = UserAgentSelector("")
        self.assertEqual(selector.get_useragent(), UserAgentSelector.DEFAULT_UA)

    @mock.patch.object(UserAgentSelector, "_append_to_ua_list")
    @mock.patch("google_translate.selectors.load_from_file")
    def test_load_from_file(self, mock_load_from_file, mock_append_to_list):
        ua_list = ["ua-1", "ua-2", "ua-3"]
        ua_file = "uafile"
        bad_ua_file = "baduafile"

        mock_load_from_file.return_value = ua_list

        selector = UserAgentSelector(user_agent_file=ua_file)

        mock_load_from_file.assert_called_once_with(ua_file)
        mock_append_to_list.assert_called_once_with(ua_list)

        mock_load_from_file.reset_mock()
        mock_append_to_list.reset_mock()

        mock_load_from_file.return_value = []

        selector = UserAgentSelector(user_agent_file=bad_ua_file)

        mock_load_from_file.assert_called_once_with(bad_ua_file)
        mock_append_to_list.assert_called_once_with([])

        self.assertEqual(selector.get_useragent(), UserAgentSelector.DEFAULT_UA)

    @mock.patch.object(UserAgentSelector, "_append_to_ua_list")
    @mock.patch.object(UserAgentSelector, "_get_from_http")
    def test_load_from_HTTP(self, mock_get_from_http, mock_append_to_list):
        ua_list = ["ua-1", "ua-2", "ua-3"]

        mock_get_from_http.return_value = ua_list

        selector = UserAgentSelector(http_mode=True)

        mock_get_from_http.assert_called_once()
        mock_append_to_list.assert_called_once_with(ua_list)

        mock_get_from_http.reset_mock()
        mock_append_to_list.reset_mock()

        mock_get_from_http.return_value = None

        selector = UserAgentSelector(http_mode=True)

        mock_get_from_http.assert_called_once()
        mock_append_to_list.assert_called_once_with(None)

        self.assertEqual(selector.get_useragent(), UserAgentSelector.DEFAULT_UA)

    def test_single_ua_mode(self):
        selector = UserAgentSelector(single_ua=True)
        self.assertEqual(selector.get_useragent(), UserAgentSelector.DEFAULT_UA)

    @mock.patch.object(UserAgentSelector, "_append_to_ua_list")
    @mock.patch.object(UserAgentSelector, "_get_from_http")
    @mock.patch("google_translate.selectors.load_from_file")
    def test_load_from_file_and_HTTP(self, mock_load_from_file, mock_get_from_http, mock_append_to_list):
        ua_list = ["ua-1", "ua-2", "ua-3"]
        ua_file = "uafile"

        calls = [mock.call(ua_list[:2]), mock.call(ua_list[2:])]

        mock_load_from_file.return_value = ua_list[:2]
        mock_get_from_http.return_value = ua_list[2:]

        selector = UserAgentSelector(user_agent_file=ua_file, http_mode=True)

        mock_load_from_file.assert_called_once_with(ua_file)
        mock_get_from_http.assert_called_once()

        mock_append_to_list.assert_has_calls(calls, any_order=True)

    def test_multiple_ua_overwrite(self):
        selector = UserAgentSelector("testua")

        # Emulate load from file & HTTP
        selector._user_agent_list = ["ua-1", "ua-2", "ua-3"]

        self.assertEqual(selector.get_useragent(), "testua")

    @mock.patch.object(UserAgentSelector, "get_useragent")
    def test_multiple_ua_single_mode(self, mock_get_useragent):
        selector = UserAgentSelector(single_ua=True)

        mock_get_useragent.assert_called_once()
        self.assertEqual(selector._user_agent, mock_get_useragent.return_value)


class TestExtra(unittest.TestCase):

    @mock.patch.object(UserAgentSelector, "_get_from_http")
    @mock.patch("google_translate.selectors.random.choice")
    def test_random_selection(self, mock_rand_choice, mock_get_from_http):
        ua_list = ["ua-1", "ua-2", "ua-3", "ua-4", "ua-5", "ua-6"]

        # Use mock to load user agents to list
        mock_get_from_http.return_value = ua_list

        selector = UserAgentSelector(http_mode=True)

        self.assertEqual(selector._user_agent_list, ua_list)

        mock_rand_choice.return_value = ua_list[0]

        self.assertEqual(selector.get_useragent(), ua_list[0])
        mock_rand_choice.assert_called_once_with(ua_list)

        mock_rand_choice.reset_mock()

        mock_rand_choice.return_value = ua_list[-1]

        self.assertEqual(selector.get_useragent(), ua_list[-1])
        mock_rand_choice.assert_called_once_with(ua_list)

    @unittest.skipUnless(TEST_FULL, b"TEST_FULL False")
    def test_load_from_HTTP_nomock(self):
        selector = UserAgentSelector(http_mode=True)

        self.assertNotEqual(len(selector._user_agent_list), 0)
        self.assertIsNotNone(selector.get_useragent())
        self.assertIn("Mozilla", selector.get_useragent())


def main():
    unittest.main()

if __name__ == '__main__':
    main()
