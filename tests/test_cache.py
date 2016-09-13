#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import sys
import os.path
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mock
    from google_translate.cache import Cache
except ImportError as error:
    print error
    sys.exit(1)

# Set up global test settings
from tests import *


class TestCacheInit(unittest.TestCase):

    def test_init_invalid_size_type(self):
        self.assertRaises(TypeError, Cache, "abc", 60.0)
        self.assertRaises(TypeError, Cache, 5.5, 60.0)

    def test_init_invalid_size_value(self):
        self.assertRaises(ValueError, Cache, 0, 60.0)

    def test_init_invalid_timeperiod_type(self):
        self.assertRaises(TypeError, Cache, 5, None)
        self.assertRaises(TypeError, Cache, 5, "abc")

    def test_init_invalid_timeperiod_value(self):
        self.assertRaises(ValueError, Cache, 5, 0.0)


class TestCachePrivateMethods(unittest.TestCase):

    @mock.patch("google_translate.cache.time.time")
    def test_valid_timestamp_true(self, mock_time):
        cache = Cache(5, 60.0)
        cache._items = {"k1": ["v1", 20.0]}

        mock_time.return_value = 50.0
        self.assertTrue(cache._valid_timestamp("k1"))
        mock_time.assert_called_once()

        mock_time.reset_mock()

        mock_time.return_value = 80.0
        self.assertTrue(cache._valid_timestamp("k1"))
        mock_time.assert_called_once()

    @mock.patch("google_translate.cache.time.time")
    def test_valid_timestamp_false(self, mock_time):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["v1", 20.0]}
        mock_time.return_value = 100.0
        self.assertFalse(cache._valid_timestamp("k1"))
        mock_time.assert_called_once()

class TestCacheSuite(unittest.TestSuite):

    def __init__(self):
        super(TestCacheSuite, self).__init__()
        self.addTest(unittest.makeSuite(TestCacheInit))
        self.addTest(unittest.makeSuite(TestCachePrivateMethods))
        self.addTest(unittest.makeSuite(TestCache))

class TestCacheExtra(unittest.TestCase):

    """docstring for TestCacheExtra"""

    def test_edit_max_size(self):
        cache = Cache(5, 60.0)

        raised = False
        try:
            cache.max_size = 50
        except AttributeError:
            raised = True

        self.assertTrue(raised)

    def test_edit_valid_period(self):
        cache = Cache(5, 60.0)

        raised = False
        try:
            cache.valid_period = 0.0
        except ValueError:
            raised = True

        self.assertTrue(raised)

        raised = False
        try:
            cache.valid_period = "abc"
        except TypeError:
            raised = True

        self.assertTrue(raised)

    def test_get_items(self):
        cache = Cache(5, 60.0)
        cache._items = {"k1": ["v1", 0.5], "k2": ["v2", 0.8]}
        self.assertEqual(sorted(cache.items()), [("k1", ["v1", 0.5]), ("k2", ["v2", 0.8])])

    def test_repr(self):
        cache = Cache(5, 60.0)
        cache._items = {"k1": ["v1", 0.5]}
        self.assertEqual(cache.__repr__(), "Cache([(u'k1', [u'v1', 0.5])])")

class TestCache(unittest.TestCase):

    """docstring for TestCache"""

    def test_size(self):
        cache = Cache(500, 60.0)
        for i in range(100):
            cache.add(i, i)

        self.assertEqual(len(cache), 100)

    def test_has_space_true(self):
        cache = Cache(5, 60.0)
        self.assertTrue(cache.has_space())

    def test_has_space_false(self):
        cache = Cache(5, 60.0)
        cache._items = {"k1": ["v1", 0.1], "k2": ["v2", 0.5], "k3": ["v3", 1.2], "k4": ["v4", 5.8], "k5": ["v5", 6.4]}

        self.assertFalse(cache.has_space())

    def test_has_key_true(self):
        cache = Cache(5, 60.0)
        cache._items = {"k1": ["data", 0.1]}
        self.assertTrue(cache.has("k1"))

    def test_has_key_false(self):
        cache = Cache(5, 60.0)
        self.assertFalse(cache.has("k2"))

    def test_get_oldest(self):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["data", 1.0], "k2": ["data", 1.5], "k3": ["data", 0.5]}
        self.assertEqual(cache.get_oldest(), "k3")

        cache._items = {"k1": ["data", 0.1], "k2": ["data", 1.0]}
        self.assertEqual(cache.get_oldest(), "k1")

    def test_get_oldest_empty_cache(self):
        cache = Cache(5, 60.0)
        self.assertIsNone(cache.get_oldest())

    @mock.patch("google_translate.cache.time.time")
    def test_add_cache_empty(self, mock_time):
        cache = Cache(5, 60.0)

        cache.add("k1", "data")
        mock_time.assert_called_once()

        self.assertEqual(cache._items, {"k1": ["data", mock_time.return_value]})

    @mock.patch.object(Cache, "get_oldest")
    @mock.patch("google_translate.cache.time.time")
    def test_add_cache_full(self, mock_time, mock_get_oldest):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["v1", 0.6], "k2": ["v2", 0.5], "k3": ["v3", 0.1], "k4": ["v4", 1.5], "k5": ["v5", 2.1]}

        mock_get_oldest.return_value = "k3"

        cache.add("k6", "v6")
        mock_get_oldest.assert_called_once()
        mock_time.assert_called_once()

        self.assertEqual(cache._items, {"k1": ["v1", 0.6], "k2": ["v2", 0.5], "k6": ["v6", mock_time.return_value], "k4": ["v4", 1.5], "k5": ["v5", 2.1]})

    @mock.patch("google_translate.cache.time.time")
    def test_add_item_already_in_cache(self, mock_time):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["v1", 0.1]}

        cache.add("k1", "v10")
        mock_time.assert_called_once()
        self.assertEqual(cache._items, {"k1": ["v10", mock_time.return_value]})

    @mock.patch.object(Cache, "_valid_timestamp")
    def test_get_item_in_cache_valid_timestamp(self, mock_valid_timestamp):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["v1", 0.1]}
        mock_valid_timestamp.return_value = True

        self.assertEqual(cache.get("k1"), "v1")
        mock_valid_timestamp.assert_called_once_with("k1")

    @mock.patch.object(Cache, "_valid_timestamp")
    def test_get_item_in_cache_invalid_timestamp(self, mock_valid_timestamp):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["v1", 0.1]}
        mock_valid_timestamp.return_value = False

        self.assertIsNone(cache.get("k1"))
        mock_valid_timestamp.assert_called_once_with("k1")

    def test_get_item_not_in_cache(self):
        cache = Cache(5, 60.0)

        self.assertIsNone(cache.get("k1"))

    @mock.patch.object(Cache, "_valid_timestamp")
    def test_remove_old(self, mock_valid_timestamp):
        cache = Cache(5, 60.0)

        items = {"k1": ["v1", 0.1], "k2": ["v2", 0.5], "k3": ["v3", 1.8], "k4": ["v4", 55.5]}
        cache._items = items

        mock_valid_timestamp.side_effect = lambda x: True if x == "k4" else False

        self.assertEqual(cache.remove_old(), 3)
        self.assertEqual(cache._items, {"k4": ["v4", 55.5]})
        mock_valid_timestamp.assert_has_calls([mock.call(key) for key in items])

    @mock.patch.object(Cache, "_valid_timestamp")
    def test_remove_old_empty_cache(self, mock_valid_timestamp):
        cache = Cache(5, 60.0)

        items = {"k1": ["v1", 0.1], "k2": ["v2", 0.5], "k3": ["v3", 1.8], "k4": ["v4", 55.5]}
        cache._items = items

        mock_valid_timestamp.return_value = True

        self.assertEqual(cache.remove_old(), 0)
        self.assertEqual(cache._items, items)
        mock_valid_timestamp.assert_has_calls([mock.call(key) for key in items])

    @mock.patch("google_translate.cache.write_dict")
    def test_store_success(self, mock_write_dict):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["v1", 0.5], "k2": ["v2", 0.9]}
        mock_write_dict.return_value = True

        self.assertTrue(cache.store("somefile"))
        mock_write_dict.assert_called_once_with("somefile", cache._items)

    @mock.patch("google_translate.cache.write_dict")
    def test_store_failure(self, mock_write_dict):
        cache = Cache(5, 60.0)

        cache._items = {"k1": ["v1", 0.5], "k2": ["v2", 0.9]}
        mock_write_dict.return_value = False

        self.assertFalse(cache.store("somefile"))
        mock_write_dict.assert_called_once_with("somefile", cache._items)

    @mock.patch("google_translate.cache.get_dict")
    def test_load_success(self, mock_get_dict):
        cache = Cache(5, 60.0)

        mock_get_dict.return_value = {"k1": ["v1", 0.5], "k2": ["v2", 0.8]}

        self.assertTrue(cache.load("somefile"))
        mock_get_dict.assert_called_once_with("somefile")
        self.assertEqual(cache._items, mock_get_dict.return_value)

    @mock.patch("google_translate.cache.get_dict")
    def test_load_failure(self, mock_get_dict):
        cache = Cache(5, 60.0)

        mock_get_dict.return_value = None

        self.assertFalse(cache.load("somefile"))
        mock_get_dict.assert_called_once_with("somefile")
        self.assertEqual(cache._items, {})

    @mock.patch("google_translate.cache.get_dict")
    def test_load_success_cache_smaller_than_file(self, mock_get_dict):
        cache = Cache(1, 60.0)

        mock_get_dict.return_value = {"k1": ["v1", 0.5], "k2": ["v2", 0.8], "k3": ["v3", 1.5]}

        self.assertTrue(cache.load("somefile"))
        mock_get_dict.assert_called_once_with("somefile")
        self.assertEqual(cache._items, {"k3": ["v3", 1.5]})


def main():
    unittest.main()


if __name__ == '__main__':
    main()
