#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import os
import sys
import json
import unittest
import logging.config

from urllib2 import URLError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import mock
    from google_translate import GoogleTranslator
except ImportError as error:
    print error
    sys.exit(1)

# Set up global test settings
from tests import *


class TestGetInfoDict(unittest.TestCase):

    def setUp(self):
        self.translator = GoogleTranslator()

    @mock.patch.object(GoogleTranslator, "_validate_language")
    @mock.patch.object(GoogleTranslator, "_do_work")
    def test_get_info_dict_default_params(self, mock_do_work, mock_val_lang):
        self.assertEqual(self.translator.get_info_dict("hello", "de"), mock_do_work.return_value)

        mock_do_work.assert_called_once_with(self.translator._get_info, "hello", mock_val_lang.return_value, mock_val_lang.return_value, "text")
        mock_val_lang.assert_has_calls([mock.call("auto"), mock.call("de", allow_auto=False)])

    @mock.patch.object(GoogleTranslator, "_validate_language")
    @mock.patch.object(GoogleTranslator, "_do_work")
    def test_get_info_dict_non_default_params(self, mock_do_work, mock_val_lang):
        self.assertEqual(self.translator.get_info_dict("hello", "de", "en", "json"), mock_do_work.return_value)

        mock_do_work.assert_called_once_with(self.translator._get_info, "hello", mock_val_lang.return_value, mock_val_lang.return_value, "json")
        mock_val_lang.assert_has_calls([mock.call("en"), mock.call("de", allow_auto=False)])

    @unittest.skipUnless(TEST_FULL, b"TEST_FULL False")
    def test_get_info_dict_full(self):

        expected_output = {
            "original_text": "house",
            "extra": {
                "verbs": {
                    "στεγάζω": ["house", "roof"],
                    "εστιώ": ["house"]
                },
                 "nouns": {
                     "σπίτι": ["home", "house"],
                     "κατοικία": ["residence", "house", "home", "dwelling", "domicile", "residency"],
                     "οικία": ["house", "home"],
                     "οίκος": ["house", "home"],
                     "βουλή": ["parliament", "house", "legislature", "diet", "State house"]
                }
            },
            "has_typo": False,
            "romanization": "house",
            "src_lang": "en",
            "translation": "σπίτι",
            "match": 1
        }

        self.assertEqual(self.translator.get_info_dict("house", "el"), expected_output)


class TestGetHeaders(unittest.TestCase):

    def assertListEqual(self, list1, list2):
        if sorted(list1) != sorted(list2):
            raise AssertionError("lists are not equal")

    def test_get_headers_default(self):
        translator = GoogleTranslator()

        self.assertListEqual(translator._get_headers(), translator._default_headers.items())

    def test_get_headers_with_user_specific_headers(self):
        translator = GoogleTranslator()

        # This should overwrite the default Host header
        translator._user_specific_headers = {"Host": "test.com"}

        expected_headers = dict(translator._default_headers)
        expected_headers["Host"] = "test.com"

        self.assertListEqual(translator._get_headers(), expected_headers.items())

    def test_get_headers_default_with_uaselector(self):
        mock_ua_selector = mock.MagicMock()
        translator = GoogleTranslator(ua_selector=mock_ua_selector)

        # Test get_useragent retvalue is not None
        mock_ua_selector.get_useragent.return_value = "user-agent1"

        expected_headers = dict(translator._default_headers)
        expected_headers["User-Agent"] = mock_ua_selector.get_useragent.return_value

        self.assertListEqual(translator._get_headers(), expected_headers.items())
        mock_ua_selector.get_useragent.assert_called_once()

        mock_ua_selector.reset_mock()

        # Test get_useragent retvalue is None
        mock_ua_selector.get_useragent.return_value = None

        self.assertListEqual(translator._get_headers(), translator._default_headers.items())
        mock_ua_selector.get_useragent.assert_called_once()

    def test_get_headers_with_user_specific_headers_and_uaselector(self):
        mock_ua_selector = mock.MagicMock()
        translator = GoogleTranslator(ua_selector=mock_ua_selector)

        # This should overwrite both the default user-agent and the uaselector
        translator._user_specific_headers = {"User-Agent": "user_spec_ua"}

        expected_headers = dict(translator._default_headers)
        expected_headers["User-Agent"] = "user_spec_ua"

        self.assertListEqual(translator._get_headers(), expected_headers.items())

class TestGetInfo(unittest.TestCase):

    @mock.patch("google_translate.translator.copy.deepcopy")
    @mock.patch("google_translate.translator.Cache.get")
    def test_get_info_cache_hit(self, mock_cache_get, mock_deepcopy):
        translator = GoogleTranslator()

        self.assertEqual(translator._get_info("test", "ru", "en"), mock_deepcopy.return_value)
        mock_cache_get.assert_called_once_with("testruen")
        mock_deepcopy.assert_called_once_with(mock_cache_get.return_value)

    @mock.patch.object(GoogleTranslator, "_try_make_request")
    @mock.patch.object(GoogleTranslator, "_build_request")
    @mock.patch("google_translate.translator.Cache.get")
    def test_get_info_invalid_request(self, mock_cache_get, mock_build_request, mock_try_make_request):
        translator = GoogleTranslator()

        mock_cache_get.return_value = None  # Simulate cache miss
        mock_try_make_request.return_value = None

        self.assertIsNone(translator._get_info("test", "ru", "en"))
        mock_cache_get.assert_called_once_with("testruen")
        mock_build_request.assert_called_once_with("test", "ru", "en")
        mock_try_make_request.assert_called_once_with(mock_build_request.return_value)

    @mock.patch.object(GoogleTranslator, "_extract_data")
    @mock.patch.object(GoogleTranslator, "_string_to_json")
    @mock.patch.object(GoogleTranslator, "_try_make_request")
    @mock.patch.object(GoogleTranslator, "_build_request")
    @mock.patch("google_translate.translator.copy.deepcopy")
    @mock.patch("google_translate.translator.parse_reply")
    @mock.patch("google_translate.translator.Cache")
    def test_get_info_valid_request(self, mock_cache, mock_parse_reply, mock_deepcopy, mock_build_request, mock_try_make_request, mock_string_to_json, mock_extract_data):
        translator = GoogleTranslator()

        mock_cache.return_value.get.return_value = None  # Simulate cache miss
        self.assertEqual(translator._get_info("test", "ru", "en"), mock_deepcopy.return_value)
        mock_cache.return_value.get.assert_called_once_with("testruen")
        mock_build_request.assert_called_once_with("test", "ru", "en")
        mock_try_make_request.assert_called_once_with(mock_build_request.return_value)
        mock_parse_reply.assert_called_once_with(mock_try_make_request.return_value, translator._encoding)
        mock_string_to_json.assert_called_once_with(mock_parse_reply.return_value)
        mock_extract_data.assert_called_once_with(mock_string_to_json.return_value)
        mock_deepcopy.assert_called_once_with(mock_extract_data.return_value)



class TestPrivateMethods(unittest.TestCase):

    """docstring for TestPrivateMethods"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_proxy(self):
        mock_proxy_selector = mock.MagicMock()

        translator = GoogleTranslator()
        self.assertIsNone(translator._get_proxy())

        translator = GoogleTranslator(proxy_selector=mock_proxy_selector)

        mock_proxy_selector.get_proxy.return_value = None
        self.assertIsNone(translator._get_proxy())
        mock_proxy_selector.get_proxy.assert_called_once()

        mock_proxy_selector.reset_mock()

        mock_proxy_selector.get_proxy.return_value = "127.0.0.1:8080"
        self.assertEqual(translator._get_proxy(), "127.0.0.1:8080")
        mock_proxy_selector.get_proxy.assert_called_once()

    @mock.patch("google_translate.translator.random.uniform")
    @mock.patch("google_translate.translator.sleep")
    def test_wait(self, mock_sleep, mock_rand_uniform):
        translator = GoogleTranslator(wait_time=10)

        translator._wait()
        mock_sleep.assert_called_once_with(10)
        mock_sleep.reset_mock()

        translator = GoogleTranslator(random_wait=True)

        translator._wait()
        mock_rand_uniform.assert_called_once_with(GoogleTranslator.WAIT_MIN, GoogleTranslator.WAIT_MAX)
        mock_sleep.assert_called_once_with(mock_rand_uniform.return_value)

    @mock.patch("google_translate.translator.json.loads")
    def test_string_to_json(self, mock_json_loads):
        translator = GoogleTranslator()

        mock_json_loads.side_effect = ValueError("json decode error")

        self.assertIsNone(translator._string_to_json("data"))
        mock_json_loads.assert_called_once_with("data")

        mock_json_loads.reset_mock()
        mock_json_loads.side_effect = None
        #mock_json_loads.return_value = [[["a","b","","",1],["","","c","d"]],"e","","",1,"",[0]]

        self.assertEqual(translator._string_to_json('[[["a","b",,,1],[,,"c","d"]],"e",,,1,,[0]]'), mock_json_loads.return_value)
        mock_json_loads.assert_called_once_with('[[["a","b","","",1],["","","c","d"]],"e","","",1,"",[0]]')

        self.assertIsNone(translator._string_to_json(123456))

    def test_extract_data(self):
        translator = GoogleTranslator()

        # Check the keys with invalid input
        basic_dictionary = {
            "translation": "",
            "original_text": "",
            "romanization": "",
            "src_lang": "",
            "match": 1.0,
            "has_typo": False,
            "extra": {}
        }
        self.assertEqual(translator._extract_data(1234), basic_dictionary)

        # Check with valid input
        inputs = [
            [
                [["T1", "o1", "", "", 0], ["", "", "r1", "R2"]],
                "",
                "fr"
            ],
            [
                [["t1", "O1", "", "", 0], ["", "", "r1"]],
                "",
                "en"
            ],
            [
                [["t1", "o1", "", "", 0]],
                ["extra"],
                "en",
                "",
                "",
                "",
                0.5,
                ["", "", "", "", "", True]
            ],
            [
                [["t1", "o1", "", "", 0]],
                [
                    ["nouns", ["w1", "w2"], [["w1", ["t1", "t2"], "", 0.44], ["w2", ["t3", "t4"]]], "ooo", 1],
                    ["adjectives", ["a1"], [["a1", ["t1", "t5"], "", 0.05]], "ooo", 3],
                    ["verbs", ["v1"], [["v1", ["t6"], "", 0.0001]], "ooo", 2]
                ],
                "en",
                "",
                "",
                "",
                1
            ],
            [
                [["t1", "o1", "", "", 0]],
                [
                    ["nouns", ["w1"], [["w1", ["t1", "t2"], "", 0.666]], "ooo", 1],
                    ["verbs", ["v1"], [["v1", ["t8"], "", 0.15]], "ooo", 2]
                ],
                "en",
                "",
                "",
                "",
                1
            ],
            [],
            [
                [
                    ["Αυτή είναι μια πολύ μακρά σειρά που\n", "This is a very long line that\n", "", "", 0],
                    ["συνεχίζει στην επόμενη.", "continues to the next one.", "", "", 0],
                    ["", "", "Aftí eínai mia polý makrá seirá pou\nsynechízei stin epómeni."]  # Romanization
                ],
                "",
                "en"
            ]
        ]

        outputs = [
                {
                    "translation": "T1",
                    "original_text": "o1",
                    "romanization": "R2",
                    "src_lang": "fr",
                    "match": 1.0,
                    "extra": {},
                    "has_typo": False
                },
                {
                    "translation": "t1",
                    "original_text": "O1",
                    "romanization": "O1",
                    "src_lang": "en",
                    "match": 1.0,
                    "extra": {},
                    "has_typo": False
                },
                {
                    "translation": "t1",
                    "original_text": "o1",
                    "romanization": "o1",
                    "src_lang": "en",
                    "match": 0.5,
                    "extra": {},
                    "has_typo": True
                },
                {
                    "translation": "t1",
                    "original_text": "o1",
                    "romanization": "o1",
                    "src_lang": "en",
                    "match": 1.0,
                    "extra": {
                        "nouns": {"w1": ["t1", "t2"], "w2": ["t3", "t4"]},
                        "adjectives": {"a1": ["t1", "t5"]},
                        "verbs": {"v1": ["t6"]}
                    },
                    "has_typo": False
                },
                {
                    "translation": "t1",
                    "original_text": "o1",
                    "romanization": "o1",
                    "src_lang": "en",
                    "match": 1.0,
                    "extra": {
                        "nouns": {"w1": ["t1", "t2"]},
                        "verbs": {"v1": ["t8"]}
                    },
                    "has_typo": False
                },
                {
                    "translation": "",
                    "original_text": "",
                    "romanization": "",
                    "src_lang": "",
                    "match": 1.0,
                    "extra": {},
                    "has_typo": False
                },
                {
                    "translation": "Αυτή είναι μια πολύ μακρά σειρά που\nσυνεχίζει στην επόμενη.",
                    "original_text": "This is a very long line that\ncontinues to the next one.",
                    "romanization": "This is a very long line that\ncontinues to the next one.",
                    "src_lang": "en",
                    "match": 1.0,
                    "extra": {},
                    "has_typo": False
                }
        ]

        for index, item in enumerate(inputs):
            self.assertEqual(translator._extract_data(item), outputs[index])


    @mock.patch.object(GoogleTranslator, "_get_proxy")
    @mock.patch.object(GoogleTranslator, "_wait")
    @mock.patch("google_translate.translator.make_request")
    def test_try_make_request_remove_proxy(self, mock_make_request, mock_wait, mock_get_proxy):
        mock_proxy_selector = mock.MagicMock()
        translator = GoogleTranslator(mock_proxy_selector)

        mock_get_proxy.side_effect = ["127.0.0.1:8080"] + [None] * (translator._retries - 1)

        mock_make_request.side_effect = URLError("invalid url")

        self.assertIsNone(translator._try_make_request("https://test.com"))
        mock_proxy_selector.remove_proxy.assert_called_once_with("127.0.0.1:8080")
        self.assertEqual(mock_wait.call_count, translator._retries - 1)

    @mock.patch.object(GoogleTranslator, "_get_headers")
    @mock.patch.object(GoogleTranslator, "_get_proxy")
    @mock.patch.object(GoogleTranslator, "_wait")
    @mock.patch("google_translate.translator.make_request")
    def test_try_make_request(self, mock_make_request, mock_wait, mock_get_proxy, mock_get_headers):
        translator = GoogleTranslator(simulate=True)

        # Test simulate case
        # make_request should return None when in simulate mode
        mock_make_request.return_value = None

        self.assertIsNone(translator._try_make_request("https://www.google.com"))
        mock_make_request.assert_called_once_with("https://www.google.com", mock_get_headers.return_value, mock_get_proxy.return_value, 10.0, True)
        mock_get_proxy.assert_called_once()
        mock_get_headers.assert_called_once()
        mock_wait.assert_not_called()

        mock_make_request.reset_mock()
        mock_get_proxy.reset_mock()
        mock_get_headers.reset_mock()

        timeout = 50.0
        retries = 10

        translator = GoogleTranslator(timeout=timeout, retries=retries)

        # Test raise URLError
        mock_make_request.side_effect = URLError("invalid url")

        make_request_calls = [mock.call("https://www.google.com", mock_get_headers.return_value, mock_get_proxy.return_value, timeout, False)] * retries

        self.assertIsNone(translator._try_make_request("https://www.google.com"))
        mock_make_request.assert_has_calls(make_request_calls)
        self.assertEqual(mock_wait.call_count, retries - 1)
        self.assertEqual(mock_get_proxy.call_count, retries)
        self.assertEqual(mock_get_headers.call_count, retries)

        mock_make_request.reset_mock()
        mock_wait.reset_mock()
        mock_get_proxy.reset_mock()
        mock_get_headers.reset_mock()

        # Test normal use case
        mock_make_request.side_effect = None

        self.assertEqual(translator._try_make_request("https://www.google.com"), mock_make_request.return_value)
        mock_make_request.assert_called_once_with("https://www.google.com", mock_get_headers.return_value, mock_get_proxy.return_value, timeout, False)
        mock_wait.assert_not_called()
        mock_get_proxy.assert_called_once()
        mock_get_headers.assert_called_once()


    @mock.patch("google_translate.translator.get_tk")
    @mock.patch("google_translate.translator.quote_unicode")
    def test_build_request(self, mock_quote, mock_gettk):
        mock_gettk.return_value = 1234
        params = "client=t&sl={0}&tl={1}&dt=t&dt=bd&dt=rm&dt=qca&ie={2}&oe={2}&tk={3}&q={4}"

        mock_quote.return_value = "test%20test"

        #Test http
        translator = GoogleTranslator(https=False)

        current_params = params.format("s2", "s1", "UTF-8", mock_gettk.return_value, mock_quote.return_value)
        expected_output = GoogleTranslator.REQUEST_URL.format(prot="http", host=GoogleTranslator.DOMAIN_NAME, params=current_params)
        self.assertEqual(translator._build_request("test test", "s1", "s2"), expected_output)

        mock_gettk.assert_called_once_with("test test")
        mock_quote.assert_called_once_with("test test", translator._encoding)

        mock_gettk.reset_mock()
        mock_quote.reset_mock()

        mock_quote.return_value = "τεστ%20τεστ"

        #Test https
        translator = GoogleTranslator()

        current_params = params.format("s2", "s1", "UTF-8", mock_gettk.return_value, mock_quote.return_value)
        expected_output = GoogleTranslator.REQUEST_URL.format(prot="https", host=GoogleTranslator.DOMAIN_NAME, params=current_params)
        self.assertEqual(translator._build_request("τεστ τεστ", "s1", "s2"), expected_output)

        mock_gettk.assert_called_once_with("τεστ τεστ")
        mock_quote.assert_called_once_with("τεστ τεστ", translator._encoding)

        mock_gettk.reset_mock()
        mock_quote.reset_mock()

        #Test different encoding
        mock_quote.return_value = "test%20test"

        translator = GoogleTranslator(encoding="ascii")

        current_params = params.format("s2", "s1", "ascii", mock_gettk.return_value, mock_quote.return_value)
        expected_output = GoogleTranslator.REQUEST_URL.format(prot="https", host=GoogleTranslator.DOMAIN_NAME, params=current_params)
        self.assertEqual(translator._build_request("test test", "s1", "s2"), expected_output)

        mock_gettk.assert_called_once_with("test test")
        mock_quote.assert_called_once_with("test test", translator._encoding)

        mock_gettk.reset_mock()
        mock_quote.reset_mock()

        #Test invalid encoding
        mock_quote.side_effect = UnicodeEncodeError(b"ascii", "", 0, 1, b"Cant encode char")

        self.assertRaises(UnicodeEncodeError, translator._build_request, "τεστ τεστ", "s1", "s2")
        mock_gettk.assert_called_once_with("τεστ τεστ")
        mock_quote.assert_called_once_with("τεστ τεστ", translator._encoding)


    def test_validate_language(self):
        translator = GoogleTranslator()

        self.assertEqual(translator._validate_language("en"), "en")
        self.assertEqual(translator._validate_language("EN"), "en")
        self.assertEqual(translator._validate_language("Ceb"), "ceb")
        self.assertEqual(translator._validate_language("GREEK"), "el")
        self.assertEqual(translator._validate_language("ZH-CN"), "zh-CN")
        self.assertEqual(translator._validate_language("CHINESE Traditional"), "zh-TW")
        self.assertEqual(translator._validate_language("AuTo"), "auto")

        self.assertRaises(ValueError, translator._validate_language, "abc")
        self.assertRaises(ValueError, translator._validate_language, "zz")
        self.assertRaises(ValueError, translator._validate_language, "zh-TB")
        self.assertRaises(ValueError, translator._validate_language, "el-lo")
        self.assertRaises(ValueError, translator._validate_language, 222)
        self.assertRaises(ValueError, translator._validate_language, "E-")
        self.assertRaises(ValueError, translator._validate_language, "AutO", False)
        self.assertRaises(ValueError, translator._validate_language, "αβγ")
        self.assertRaises(ValueError, translator._validate_language, "中文")

    @mock.patch("google_translate.translator.quote_unicode")
    def test_validate_word(self, mock_quote_unicode):
        translator = GoogleTranslator()

        self.assertRaises(ValueError, translator._validate_word, 1234)

        mock_quote_unicode.return_value = "a" * GoogleTranslator.MAX_INPUT_SIZE
        self.assertRaises(ValueError, translator._validate_word, "a")
        mock_quote_unicode.assert_called_once_with("a", translator._encoding)

        mock_quote_unicode.reset_mock()

        mock_quote_unicode.return_value = "a" * (GoogleTranslator.MAX_INPUT_SIZE + 1)
        self.assertRaises(ValueError, translator._validate_word, "a")
        mock_quote_unicode.assert_called_once_with("a", translator._encoding)

    @mock.patch.object(GoogleTranslator, "_get_info")
    #@mock.patch.object(GoogleTranslator, "_validate_language")
    #@mock.patch.object(GoogleTranslator, "_validate_word")
    def test_translate(self, mock_get_info):
        translator = GoogleTranslator()

        def reset_mocks():
            #mock_val_word.reset_mock()
            #mock_val_lang.reset_mock()
            mock_get_info.reset_mock()

        def check_calls(word, dlang, slang):
            #mock_val_word.assert_called_once_with(word)
            #mock_val_lang.assert_has_calls([mock.call(dlang, allow_auto=False), mock.call(slang)], any_order=True)
            mock_get_info.assert_called_once_with(word, dlang, slang)

        # Test src_lang = dst_lang
        self.assertEqual(translator._translate("test", "en", "en", False), "test")
        #mock_val_word.assert_called_once_with("test")
        #mock_val_lang.assert_has_calls([mock.call("en", allow_auto=False), mock.call("en")], any_order=True)
        mock_get_info.assert_not_called()

        reset_mocks()

        # Make _validate_language not return the same item
        #def fake_validate_lang(lang, allow_auto=False):
            #return lang
        #mock_val_lang.side_effect = fake_validate_lang

        # Test data = None
        mock_get_info.return_value = None
        self.assertIsNone(translator._translate("test", "ru", "en", False))
        check_calls("test", "ru", "en")
        reset_mocks()

        # Test data != None
        mock_get_info.return_value = {
            "original_text": "test",
            "translation": "test",
            "extra": {"nouns": {"n1": ["t1", "t2", "t3"]}},
            "has_typo": False
        }

        # Test no typo, no additional, translation not found
        #self.assertIsNone(translator._translate("test", "ru", "en", False))
        #check_calls("test", "ru", "en")
        #reset_mocks()

        # Test no typo, no additional, translation found
        mock_get_info.return_value["translation"] = "rrrr"

        self.assertEqual(translator._translate("test", "ru", "en", False), mock_get_info.return_value["translation"])
        check_calls("test", "ru", "en")
        reset_mocks()

        # Test no typo, with additional, translation found
        self.assertEqual(translator._translate("test", "ru", "en", True), mock_get_info.return_value["extra"])
        check_calls("test", "ru", "en")
        reset_mocks()

        # Test with typo
        mock_get_info.return_value["has_typo"] = True
        self.assertIsNone(translator._translate("testt", "ru", "en", False))
        check_calls("testt", "ru", "en")

    @mock.patch.object(GoogleTranslator, "_get_info")
    #@mock.patch.object(GoogleTranslator, "_validate_word")
    @mock.patch("google_translate.translator.TwoWayOrderedDict")
    def test_detect(self, mock_twodict, mock_get_info):
        translator = GoogleTranslator()

        # Test data = None
        mock_get_info.return_value = None

        self.assertIsNone(translator._detect("test"))
        #mock_val_word.assert_called_once_with("test")
        mock_get_info.assert_called_once_with("test", "en", "auto")

        #mock_val_word.reset_mock()
        mock_get_info.reset_mock()

        # Test data != None
        mock_get_info.return_value = {"src_lang": "en"}

        # No KeyError
        mock_twodict.return_value.__getitem__.return_value = "english"

        self.assertEqual(translator._detect("test"), "english")
        #mock_val_word.assert_called_once_with("test")
        mock_get_info.assert_called_once_with("test", "en", "auto")

        #mock_val_word.reset_mock()
        mock_get_info.reset_mock()

        # With KeyError
        mock_twodict.return_value.__getitem__.side_effect = KeyError()

        self.assertEqual(translator._detect("test"), "en")
        #mock_val_word.assert_called_once_with("test")
        mock_get_info.assert_called_once_with("test", "en", "auto")

    @mock.patch.object(GoogleTranslator, "_get_info")
    #@mock.patch.object(GoogleTranslator, "_validate_language")
    #@mock.patch.object(GoogleTranslator, "_validate_word")
    def test_romanize(self, mock_get_info):
        translator = GoogleTranslator()

        # Test data = None
        mock_get_info.return_value = None

        self.assertIsNone(translator._romanize("test", "ru"))
        #mock_val_word.assert_called_once_with("test")
        #mock_val_lang.assert_has_calls([mock.call("ru", allow_auto=False), mock.call("en")], any_order=True)
        #mock_val_lang.assert_called_once_with("ru")
        mock_get_info.assert_called_once_with("test", "en", "ru")

        #mock_val_word.reset_mock()
        #mock_val_lang.reset_mock()
        mock_get_info.reset_mock()

        # Test data != None
        mock_get_info.return_value = {"original_text": "test", "romanization": "rom", "has_typo": True}

        # With typo
        self.assertIsNone(translator._romanize("testt", "ru"))
        #mock_val_word.assert_called_once_with("testt")
        #mock_val_lang.assert_has_calls([mock.call("ru", allow_auto=False), mock.call("en")], any_order=True)
        #mock_val_lang.assert_called_once_with("ru")
        mock_get_info.assert_called_once_with("testt", "en", "ru")

        #mock_val_word.reset_mock()
        #mock_val_lang.reset_mock()
        mock_get_info.reset_mock()

        # No typo
        mock_get_info.return_value["has_typo"] = False
        self.assertEqual(translator._romanize("test", "ru"), mock_get_info.return_value["romanization"])
        #mock_val_word.assert_called_once_with("test")
        #mock_val_lang.assert_has_calls([mock.call("ru", allow_auto=False), mock.call("en")], any_order=True)
        #mock_val_lang.assert_called_once_with("ru")
        mock_get_info.assert_called_once_with("test", "en", "ru")

    @mock.patch.object(GoogleTranslator, "_get_info")
    #@mock.patch.object(GoogleTranslator, "_validate_language")
    #@mock.patch.object(GoogleTranslator, "_validate_word")
    def test_word_exists(self, mock_get_info):
        translator = GoogleTranslator()

        # Test data = None
        mock_get_info.return_value = None
        self.assertFalse(translator._word_exists("test", "en"))

        #mock_val_word.assert_called_once_with("test")
        #mock_val_lang.assert_called_once_with("en", allow_auto=False)
        # 'af' is the first language in lang_db
        mock_get_info.assert_called_once_with("test", "af", "en")

        #mock_val_word.reset_mock()
        #mock_val_lang.reset_mock()
        mock_get_info.reset_mock()

        # Test data != None
        mock_get_info.return_value = {"original_text": "test", "translation": "rrrr", "has_typo": True}

        # With typo
        self.assertFalse(translator._word_exists("testt", "en"))

        #mock_val_word.assert_called_once_with("testt")
        #mock_val_lang.assert_called_once_with("en", allow_auto=False)
        mock_get_info.assert_called_once_with("testt", "af", "en")

        #mock_val_word.reset_mock()
        #mock_val_lang.reset_mock()
        mock_get_info.reset_mock()

        # No typo
        mock_get_info.return_value["has_typo"] = False
        self.assertTrue(translator._word_exists("test", "en"))

        #mock_val_word.assert_called_once_with("test")
        #mock_val_lang.assert_called_once_with("en", allow_auto=False)
        mock_get_info.assert_called_once_with("test", "af", "en")

        #mock_val_word.reset_mock()
        #mock_val_lang.reset_mock()
        mock_get_info.reset_mock()

        # translation = original text
        #mock_get_info.return_value["translation"] = "test"

        #self.assertFalse(translator._word_exists("test", "en"))

        #mock_val_word.assert_called_once_with("test")
        #mock_val_lang.assert_called_once_with("en", allow_auto=False)
        #mock_get_info.assert_called_once_with("test", "af", mock_val_lang.return_value)

    @mock.patch("google_translate.translator.json.dumps")
    def test_convert_output(self, mock_json_dumps):
        translator = GoogleTranslator()

        # Test raises
        self.assertRaises(ValueError, translator._convert_output, "word", "translation", "invalid")
        self.assertRaises(ValueError, translator._convert_output, "word", "translation", 123456)

        # Test 'text' output
        self.assertEqual(translator._convert_output("word", "trans", "text"), "trans")
        self.assertEqual(translator._convert_output("word", {"nouns": {"w1": ["t1"]}}, "text"), {"nouns": {"w1": ["t1"]}})
        self.assertEqual(translator._convert_output(["word1", "word2"], ["trans1", "trans2"], "text"), ["trans1", "trans2"])
        self.assertEqual(translator._convert_output(["word1", "word2"], [{"nouns": {"w1": ["t1"]}}, {"verbs": {"w2": ["t2"]}}], "text"), [{"nouns": {"w1": ["t1"]}}, {"verbs": {"w2": ["t2"]}}])

        # Test 'dict' output
        self.assertEqual(translator._convert_output("word", "trans", "dict"), {"word": "trans"})
        self.assertEqual(translator._convert_output("word", {"nouns": {"w1": ["t1"]}}, "dict"), {"word": {"nouns": {"w1": ["t1"]}}})
        self.assertEqual(translator._convert_output(["word1", "word2"], ["trans1", "trans2"], "dict"), {"word1": "trans1", "word2": "trans2"})
        self.assertEqual(translator._convert_output(["word1", "word2"], [{"nouns": {"w1": ["t1"]}}, {"verbs": {"w2": ["t2"]}}], "dict"), {"word1": {"nouns": {"w1": ["t1"]}}, "word2": {"verbs": {"w2": ["t2"]}}})

        # Test 'json' output
        self.assertEqual(translator._convert_output("word", "trans", "json"), mock_json_dumps.return_value)
        mock_json_dumps.assert_called_once_with({"word": "trans"}, indent=4, ensure_ascii=False)
        mock_json_dumps.reset_mock()

        self.assertEqual(translator._convert_output("word", {"nouns": {"w1": ["t1"]}}, "json"), mock_json_dumps.return_value)
        mock_json_dumps.assert_called_once_with({"word": {"nouns": {"w1": ["t1"]}}}, indent=4, ensure_ascii=False)
        mock_json_dumps.reset_mock()

        self.assertEqual(translator._convert_output(["word1", "word2"], ["trans1", "trans2"], "json"), mock_json_dumps.return_value)
        mock_json_dumps.assert_called_once_with({"word1": "trans1", "word2": "trans2"}, indent=4, ensure_ascii=False)
        mock_json_dumps.reset_mock()

        self.assertEqual(translator._convert_output(["word1", "word2"], [{"nouns": {"w1": ["t1"]}}, {"verbs": {"w2": ["t2"]}}], "json"), mock_json_dumps.return_value)
        mock_json_dumps.assert_called_once_with({"word1": {"nouns": {"w1": ["t1"]}}, "word2": {"verbs": {"w2": ["t2"]}}}, indent=4, ensure_ascii=False)
        mock_json_dumps.reset_mock()

    @mock.patch.object(GoogleTranslator, "_wait")
    @mock.patch.object(GoogleTranslator, "_validate_word")
    @mock.patch.object(GoogleTranslator, "_convert_output")
    def test_do_work(self, mock_convert_output, mock_validate_word, mock_wait):
        translator = GoogleTranslator()

        params1 = ("param1", "param2", "param3", "param4")
        params2 = (["w1", "w2", "w3"], "param2", "param3")
        mock_function = mock.MagicMock()

        # Test word not list
        self.assertEqual(translator._do_work(mock_function, *params1), mock_convert_output.return_value)
        mock_function.assert_called_once_with(*params1[:-1])
        mock_convert_output.assert_called_once_with(params1[0], mock_function.return_value, params1[-1])
        mock_validate_word.assert_called_once_with("param1")

        mock_validate_word.reset_mock()
        mock_convert_output.reset_mock()
        mock_function.reset_mock()

        # Test word list
        self.assertEqual(translator._do_work(mock_function, *params2), mock_convert_output.return_value)
        mock_function.assert_has_calls([mock.call(item, *params2[1:-1]) for item in params2[0]])
        mock_convert_output.assert_called_once_with(params2[0], [mock_function.return_value] * len(params2[0]), params2[-1])
        mock_validate_word.assert_has_calls([mock.call(item) for item in params2[0]])
        self.assertEqual(mock_wait.call_count, len(params2[0]) - 1)

class TestTranslate(unittest.TestCase):

    """docstring for TestTranslate"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch.object(GoogleTranslator, "_validate_language")
    @mock.patch.object(GoogleTranslator, "_do_work")
    def test_translate(self, mock_do_work, mock_val_lang):
        translator = GoogleTranslator()

        self.assertEqual(translator.translate("test", "ru"), mock_do_work.return_value)
        mock_val_lang.assert_has_calls([mock.call("auto"), mock.call("ru", allow_auto=False)])
        mock_do_work.assert_called_once_with(translator._translate, "test", mock_val_lang.return_value, mock_val_lang.return_value, False, "text")

        mock_do_work.reset_mock()
        mock_val_lang.reset_mock()

        self.assertEqual(translator.translate("test", "ru", src_lang="en", additional=True, output="dict"), mock_do_work.return_value)
        mock_val_lang.assert_has_calls([mock.call("en"), mock.call("ru", allow_auto=False)])
        mock_do_work.assert_called_once_with(translator._translate, "test", mock_val_lang.return_value, mock_val_lang.return_value, True, "dict")

        # Test invalid 'additional' param
        self.assertRaises(ValueError, translator.translate, "test", "ru", "en", 1234)

    @unittest.skipUnless(TEST_FULL, b"TEST_FULL False")
    def test_translate_full(self):
        translator = GoogleTranslator()

        self.assertEqual(translator.translate("house", "de"), "Haus")
        self.assertEqual(translator.translate("σπίτι", "en"), "home")
        self.assertEqual(
                translator.translate("house", "el", additional=True),
                {
                    "verbs": {
                        "στεγάζω": ["house", "roof"],
                        "εστιώ": ["house"]
                    },
                    "nouns": {
                        "σπίτι": ["home", "house"],
                        "κατοικία": ["residence", "house", "home", "dwelling", "domicile", "residency"],
                        "οικία": ["house", "home"],
                        "οίκος": ["house", "home"],
                        "βουλή": ["parliament", "house", "legislature", "diet", "State house"]
                    }
                }
        )


class TestDetect(unittest.TestCase):

    """docstring for TestDetect"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch.object(GoogleTranslator, "_do_work")
    def test_detect(self, mock_do_work):
        translator = GoogleTranslator()

        self.assertEqual(translator.detect("test"), mock_do_work.return_value)
        mock_do_work.assert_called_once_with(translator._detect, "test", "text")

        mock_do_work.reset_mock()

        self.assertEqual(translator.detect("test", output="dict"), mock_do_work.return_value)
        mock_do_work.assert_called_once_with(translator._detect, "test", "dict")

    @unittest.skipUnless(TEST_FULL, b"TEST_FULL False")
    def test_detect_full(self):
        translator = GoogleTranslator()

        self.assertEqual(translator.detect("hi"), "english")
        self.assertEqual(translator.detect("犬"), "japanese")
        self.assertEqual(translator.detect("σπίτη"), "greek")  # With typo

class TestRomanize(unittest.TestCase):

    """docstring for Romanize"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch.object(GoogleTranslator, "_validate_language")
    @mock.patch.object(GoogleTranslator, "_do_work")
    def test_romanize(self, mock_do_work, mock_val_lang):
        translator = GoogleTranslator()

        self.assertEqual(translator.romanize("test"), mock_do_work.return_value)
        mock_val_lang.assert_called_once_with("auto")
        mock_do_work.assert_called_once_with(translator._romanize, "test", mock_val_lang.return_value, "text")

        mock_do_work.reset_mock()
        mock_val_lang.reset_mock()

        self.assertEqual(translator.romanize("test", "en", "json"), mock_do_work.return_value)
        mock_val_lang.assert_called_once_with("en")
        mock_do_work.assert_called_once_with(translator._romanize, "test", mock_val_lang.return_value, "json")

    @unittest.skipUnless(TEST_FULL, b"TEST_FULL False")
    def test_romanize_full(self):
        translator = GoogleTranslator()

        self.assertEqual(translator.romanize("σπίτι"), "spíti")
        self.assertEqual(translator.romanize("дом"), "dom")
        self.assertEqual(translator.romanize("家", "japanese"), "Ie")
        self.assertEqual(translator.romanize("house"), "house")
        self.assertEqual(translator.romanize("hello"), "hello")
        self.assertIsNone(translator.romanize("σπίτη"))  # With typo

class TestExists(unittest.TestCase):

    """docstring for TestExists"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @mock.patch.object(GoogleTranslator, "_validate_language")
    @mock.patch.object(GoogleTranslator, "_do_work")
    def test_exists(self, mock_do_work, mock_val_lang):
        translator = GoogleTranslator()

        self.assertEqual(translator.word_exists("test"), mock_do_work.return_value)
        mock_val_lang.assert_called_once_with("en", allow_auto=False)
        mock_do_work.assert_called_once_with(translator._word_exists, "test", mock_val_lang.return_value, "text")

        mock_do_work.reset_mock()
        mock_val_lang.reset_mock()

        self.assertEqual(translator.word_exists("test", lang="ru", output="dict"), mock_do_work.return_value)
        mock_val_lang.assert_called_once_with("ru", allow_auto=False)
        mock_do_work.assert_called_once_with(translator._word_exists, "test", mock_val_lang.return_value, "dict")

    @unittest.skipUnless(TEST_FULL, b"TEST_FULL False")
    def test_exists_full(self):
        translator = GoogleTranslator()

        self.assertTrue(translator.word_exists("computer"))
        self.assertTrue(translator.word_exists("σπιτι", "el"))
        self.assertFalse(translator.word_exists("bockpack", "en"))
        self.assertFalse(translator.word_exists("σπίτι", "en"))

class TestExtra(unittest.TestCase):

    """docstring for TestExtra"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_add_header(self):
        translator = GoogleTranslator()

        self.assertEqual(translator._user_specific_headers, {})
        translator.add_header(("header", "value"))
        self.assertEqual(translator._user_specific_headers, {"header": "value"})

    def test_add_header_invalid_input(self):
        translator = GoogleTranslator()

        self.assertRaises(ValueError, translator.add_header, 1234)
        self.assertRaises(ValueError, translator.add_header, ("header", "value", "value"))
        self.assertRaises(ValueError, translator.add_header, (0, "value"))
        self.assertRaises(ValueError, translator.add_header, ("header", 0))

class TestGoogleTranslatorInitiation(unittest.TestCase):

    """docstring for TestGoogleTranslatorInitiation"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    #@mock.patch("google_translate.translator.CacheDict")
    @mock.patch("google_translate.translator.Cache")
    @mock.patch("google_translate.translator.TwoWayOrderedDict")
    @mock.patch("google_translate.translator.load_from_file")
    #@mock.patch("google_translate.translator.get_absolute_path")
    #@mock.patch("google_translate.translator.os.path.join")
    def test_init(self, mock_load_from_file, mock_twodict, mock_cache):
        mock_load_from_file.return_value = ["Lang1:code1", "Lang2:code2", "Lang3:code3"]

        translator = GoogleTranslator()

        mock_cache.assert_called_once_with(GoogleTranslator.MAX_CACHE_SIZE, GoogleTranslator.CACHE_VALID_PERIOD)
        mock_twodict.assert_called_once_with(auto="auto")
        #mock_get_abspath.assert_called_once_with(google_translate.translator.__file__)
        #mock_ospath_join.assert_called_once_with(mock_get_abspath.return_value, "data", GoogleTranslator.LANGUAGES_DB)
        mock_load_from_file.assert_called_once_with(GoogleTranslator.LANGUAGES_DB)

        mock_calls = []
        for item in mock_load_from_file.return_value:
            lang, code = item.split(':')
            mock_calls.append(mock.call(lang.lower(), code))

        mock_twodict.return_value.__setitem__.assert_has_calls(mock_calls)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
