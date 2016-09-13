Examples
========

Below are some basic examples. See the :doc:`API <api>` page for more details.

Translate
---------

  Translate single word::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    print translator.translate("hello world", "fr")

  Translate multiple words::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()

    words_to_translate = ["car", "text", "pencil"]
    translated_words = translator.translate(words_to_translate, "russian")

  Translate multiple words and get dictionary output::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()

    words_to_translate = ["car", "text", "pencil"]
    translation_dict = translator.translate(words_to_translate, "russian", output="dict")

    print translation_dict  # {'car': 'автомобиль', 'pencil': 'карандаш', 'text': 'текст'}

Additional Translations
-----------------------

  Get additional translations in json format::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    print translator.translate("house", "greek", additional=True, output="json")

Detect Source Language
----------------------

  Detect source language single word::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    print translator.detect("hello world")

  Detect source language multiple words::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    languages = translator.detect(["hello", "καλησπέρα", "こんにちは"])

    for lang in languages: print lang  # 'english' 'greek' 'japanese'

Detect typos
------------

  Detect typos single word::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    print translator.word_exists("computor")  # Returns False

  Detect typos single word with language specified::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    print translator.word_exists("καλησπέρα", "greek")  # Returns True

Text romanization
-----------------

  Romanize multiple words::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    rom_words = translator.romanize(["σπίτι", "дом"])

    print rom_words  # [u'spíti', u'dom']

Python logging
--------------

  Simple use case::

    import logging
    from google_translate import GoogleTranslator

    logging.basicConfig(level=logging.DEBUG)

    translator = GoogleTranslator()
    translator.translate("log", "ja")

Proxy
-----

  Use single proxy::

    from google_translate import GoogleTranslator, ProxySelector

    proxy_selector = ProxySelector("127.0.0.1:1337")
    translator = GoogleTranslator(proxy_selector)

    # do other stuff

  Use multiple proxies from file (one per line)::

    from google_translate import GoogleTranslator, ProxySelector

    proxy_selector = ProxySelector(proxy_file="proxies")
    translator = GoogleTranslator(proxy_selector)

    # do other stuff

  Use multiple proxies from file with random selection::

    from google_translate import GoogleTranslator, ProxySelector

    proxy_selector = ProxySelector(proxy_file="proxies", random_selection=True)
    translator = GoogleTranslator(proxy_selector)

    # do other stuff

User-Agent
----------

  Specify single user-agent to use::

    from google_translate import GoogleTranslator, UserAgentSelector

    ua_selector = UserAgentSelector("my-user-agent")
    translator = GoogleTranslator(ua_selector=ua_selector)

    # do other stuff

  Load user-agents from the Internet::

    from google_translate import GoogleTranslator, UserAgentSelector

    ua_selector = UserAgentSelector(http_mode=True)
    translator = GoogleTranslator(ua_selector=ua_selector)

    # do other stuff

Caching
-------

  Store translation cache to file::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()

    # do stuff here

    translator.cache.store("mycache")

  Load translation cache from file::

    from google_translate import GoogleTranslator

    translator = GoogleTranslator()
    translator.cache.load("mycache")

    # do other stuff

Advanced
--------

  Translate .txt file content line by line::

    from google_translate import GoogleTranslator

    with open("file.txt") as input_file:
        content = [line.rstrip() for line in input_file]

    translator = GoogleTranslator()

    tcontent = translator.translate(content, "french")

    # When an error occurs GoogleTranslator returns None
    tcontent = [line.encode("utf-8") for line in tcontent if line is not None]

    with open("trans-file.txt", "w") as output_file:
        output_file.writelines(["%s\n" for line in tcontent])

  Use multiple user-agents with multiple proxies (random selection)

  and prevent sending requests without a proxy::

    from google_translate import (
        GoogleTranslator,
        UserAgentSelector,
        ProxySelector
    )

    uselector = UserAgentSelector(http_mode=True)

    pselector = ProxySelector(proxy_file="proxies",
                              prevent_fallback=True,
                              random_selection=True)

    translator = GoogleTranslator(pselector, uselector)

    # do other stuff here
