#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import sys
import os.path
import unittest
import logging.config

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mock
    from google_translate import ProxySelector
except ImportError as error:
    print error
    sys.exit(1)

# Set up global test settings
from tests import *


class TestStaticMethods(unittest.TestCase):

    """docstring for TestStaticMethods"""

    def test_is_valid_proxy_true(self):
        self.assertTrue(ProxySelector.is_valid_proxy("127.0.0.1:8080"))
        self.assertTrue(ProxySelector.is_valid_proxy("192.168.0.0:65535"))
        self.assertTrue(ProxySelector.is_valid_proxy("80.80.80.80:1337"))

    def test_is_valid_proxy_false(self):
        self.assertFalse(ProxySelector.is_valid_proxy("1.1.1.1.1:5050"))
        self.assertFalse(ProxySelector.is_valid_proxy("8.8.8.8:65536"))
        self.assertFalse(ProxySelector.is_valid_proxy("1.1.1.1:0000"))
        self.assertFalse(ProxySelector.is_valid_proxy("1.1.1.1:-100"))
        self.assertFalse(ProxySelector.is_valid_proxy("abcdefg"))
        self.assertFalse(ProxySelector.is_valid_proxy(""))
        self.assertFalse(ProxySelector.is_valid_proxy(None))

class TestGetProxy(unittest.TestCase):

    def setUp(self):
        self.user_proxy = "8.8.8.8:1337"
        self.proxy_list = ["8.8.8.8:1", "8.8.8.8:2", "8.8.8.8:3", "8.8.8.8:4"]
        self.list_length = len(self.proxy_list)

    def test_get_default_case(self):
        selector = ProxySelector()
        self.assertIsNone(selector.get_proxy())

    def test_get_with_single_proxy(self):
        selector = ProxySelector()
        selector._proxy = self.user_proxy
        self.assertEqual(selector.get_proxy(), self.user_proxy)

    def test_get_with_multiple_proxies_norm(self):
        selector = ProxySelector()
        selector._proxy_list = self.proxy_list

        for index in range(self.list_length * 2):
            item_index = index % self.list_length

            self.assertEqual(selector.get_proxy(), self.proxy_list[item_index])

    @mock.patch("google_translate.selectors.random.choice")
    def test_get_with_multiple_proxies_rand(self, mock_rand_choice):
        selector = ProxySelector(random_selection=True)
        selector._proxy_list = self.proxy_list

        mock_rand_choice.return_value = self.proxy_list[1]

        self.assertEqual(selector.get_proxy(), self.proxy_list[1])
        mock_rand_choice.assert_called_once_with(self.proxy_list)

        mock_rand_choice.reset_mock()

        mock_rand_choice.return_value = self.proxy_list[-1]

        self.assertEqual(selector.get_proxy(), self.proxy_list[-1])
        mock_rand_choice.assert_called_once_with(self.proxy_list)

    def test_get_with_multiple_proxies_overwrite(self):
        selector = ProxySelector()
        selector._proxy = self.user_proxy
        selector._proxy_list = self.proxy_list

        for _ in range(self.list_length * 2):
            self.assertEqual(selector.get_proxy(), self.user_proxy)


class TestRemove(unittest.TestCase):

    def setUp(self):
        self.user_proxy = "8.8.8.8:1337"
        self.proxy_list = ["8.8.8.8:1", "8.8.8.8:2"]

    def test_remove_inputs(self):
        selector = ProxySelector(self.user_proxy)

        # Test with invalid proxy
        self.assertFalse(selector.remove_proxy(123456))
        self.assertIsNotNone(selector._proxy)

        # Test with valid proxy

        # Proxy not exist
        self.assertFalse(selector.remove_proxy("127.0.0.1:1337"))
        self.assertIsNotNone(selector._proxy)

        # Proxy exist
        self.assertTrue(selector.remove_proxy("8.8.8.8:1337"))
        self.assertIsNone(selector._proxy)

    def test_remove_with_single_proxy(self):
        selector = ProxySelector()
        selector._proxy = self.user_proxy

        self.assertTrue(selector.remove_proxy(self.user_proxy))
        self.assertIsNone(selector._proxy)

    def test_remove_with_multiple_proxies(self):
        selector = ProxySelector()
        selector._proxy_list = self.proxy_list

        self.assertTrue(selector.remove_proxy(self.proxy_list[1]))
        self.assertEqual(selector._proxy_list, ["8.8.8.8:1"])

        self.assertTrue(selector.remove_proxy(self.proxy_list[0]))
        self.assertEqual(selector._proxy_list, [])

    def test_remove_with_single_proxy_fallback_prevention(self):
        selector = ProxySelector(prevent_fallback=True)
        selector._proxy = self.user_proxy

        self.assertFalse(selector.remove_proxy(self.user_proxy))
        self.assertEqual(selector._proxy, self.user_proxy)

    def test_remove_with_multiple_proxies_fallback_prevention(self):
        selector = ProxySelector(prevent_fallback=True)
        selector._proxy_list = self.proxy_list

        self.assertTrue(selector.remove_proxy(self.proxy_list[1]))
        self.assertEqual(selector._proxy_list, ["8.8.8.8:1"])

        self.assertFalse(selector.remove_proxy(self.proxy_list[0]))
        self.assertEqual(selector._proxy_list, ["8.8.8.8:1"])

    def test_remove_with_multiple_proxies_overwrite(self):
        selector = ProxySelector()
        selector._proxy = self.user_proxy
        selector._proxy_list = self.proxy_list

        self.assertTrue(selector.remove_proxy(self.proxy_list[0]))
        self.assertEqual(selector._proxy, self.user_proxy)
        self.assertEqual(selector._proxy_list, ["8.8.8.8:2"])

        self.assertTrue(selector.remove_proxy(self.user_proxy))
        self.assertIsNone(selector._proxy)
        self.assertEqual(selector._proxy_list, ["8.8.8.8:2"])

        self.assertTrue(selector.remove_proxy(self.proxy_list[0]))
        self.assertIsNone(selector._proxy)
        self.assertEqual(selector._proxy_list, [])

    def test_remove_with_multiple_proxies_overwrite_fallback_prevention(self):
        selector = ProxySelector(prevent_fallback=True)
        selector._proxy = self.user_proxy
        selector._proxy_list = self.proxy_list

        self.assertTrue(selector.remove_proxy(self.proxy_list[0]))
        self.assertEqual(selector._proxy, self.user_proxy)
        self.assertEqual(selector._proxy_list, ["8.8.8.8:2"])

        self.assertTrue(selector.remove_proxy(self.user_proxy))
        self.assertIsNone(selector._proxy)
        self.assertEqual(selector._proxy_list, ["8.8.8.8:2"])

        self.assertFalse(selector.remove_proxy(self.proxy_list[0]))
        self.assertIsNone(selector._proxy)
        self.assertEqual(selector._proxy_list, ["8.8.8.8:2"])

        selector._proxy = self.user_proxy

        self.assertTrue(selector.remove_proxy(self.proxy_list[0]))
        self.assertEqual(selector._proxy, self.user_proxy)
        self.assertEqual(selector._proxy_list, [])

        self.assertFalse(selector.remove_proxy(self.user_proxy))
        self.assertEqual(selector._proxy, self.user_proxy)
        self.assertEqual(selector._proxy_list, [])

    def test_remove_reset_counter(self):
        selector = ProxySelector()

        selector._proxy_list = ["A", "B", "C"]
        selector._proxy_counter = 1  # Point the counter to 'B'

        selector.remove_proxy("A")
        self.assertEqual(selector._proxy_counter, 0)

        selector._proxy_list = ["A", "B", "C"]
        selector._proxy_counter = 1

        selector.remove_proxy("B")
        self.assertEqual(selector._proxy_counter, 1)

        selector._proxy_list = ["A", "B", "C"]
        selector._proxy_counter = 1

        selector.remove_proxy("C")
        self.assertEqual(selector._proxy_counter, 1)

        selector._proxy_list = ["A", "B", "C"]
        selector._proxy_counter = 0

        selector.remove_proxy("A")
        self.assertEqual(selector._proxy_counter, 0)


@mock.patch.object(ProxySelector, "is_valid_proxy")
@mock.patch("google_translate.selectors.load_from_file")
class TestProxySelectorInit(unittest.TestCase):

    """docstring for TestObjectState"""

    def setUp(self):
        self.proxy_list = [
            "127.0.0.1:3030",  # duplicate
            "127.0.0.1:3030",  # duplicate
            "127.0.0.1:8080",
            "127.0.0.2:5050",
            "127.0.0.9:1337"
        ]
        self.proxy = "1.1.1.1:8080"
        self.file_exists = "somefile"
        self.file_not_exists = "someotherfile"

        self.mock_calls = [mock.call(item) for item in self.proxy_list[1:]]
        self.mock_calls.append(mock.call(self.proxy))

    def test_user_specified_proxy(self, mock_load_from_file, mock_valid_proxy):
        selector = ProxySelector(self.proxy)

        self.assertEqual(selector._proxy, self.proxy)
        mock_load_from_file.assert_not_called()
        mock_valid_proxy.assert_called_once_with(self.proxy)

    def test_multiple_from_file(self, mock_load_from_file, mock_valid_proxy):
        # Test file exists
        mock_load_from_file.return_value = self.proxy_list

        selector = ProxySelector(proxy_file=self.file_exists)

        self.assertEqual(selector._proxy_list, self.proxy_list[1:])
        mock_load_from_file.assert_called_once_with(self.file_exists)
        mock_valid_proxy.assert_has_calls(self.mock_calls[:-1], any_order=True)

        mock_load_from_file.reset_mock()
        mock_valid_proxy.reset_mock()

        # Test file not exists
        mock_load_from_file.return_value = []

        selector = ProxySelector(proxy_file=self.file_not_exists)

        self.assertEqual(selector._proxy_list, [])
        mock_load_from_file.assert_called_once_with(self.file_not_exists)
        mock_valid_proxy.assert_called_once_with(None)

    def test_multiple_from_file_overwrite(self, mock_load_from_file, mock_valid_proxy):
        mock_load_from_file.return_value = self.proxy_list

        selector = ProxySelector(self.proxy, self.file_exists)

        self.assertEqual(selector._proxy, self.proxy)
        self.assertEqual(selector._proxy_list, self.proxy_list[1:])

        mock_load_from_file.assert_called_once_with(self.file_exists)
        mock_valid_proxy.assert_has_calls(self.mock_calls, any_order=True)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
