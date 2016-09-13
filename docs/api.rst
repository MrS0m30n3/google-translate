API
===

:py:class:`google_translate.GoogleTranslator`

:py:class:`google_translate.UserAgentSelector`

:py:class:`google_translate.ProxySelector`

:py:class:`google_translate.cache.Cache`

.. raw:: html

   <br>

.. note:: Valid output types are: **text, dict, json**

.. note:: Source and destination language can be either in the short format (e.g. "en")

    or in long format (e.g. "english"). Source language can also take the 'auto' value.

Info dictionary structure example::

    {
        "original_text": "word",
        "translation": "translated-word",
        "romanization": "romanized-word",
        "has_typo": False,
        "src_lang": "en",
        "extra": {
            "verbs": {
                "verb1": ["trans1"],
                "verb2": ["trans1", "trans2", "trans3", "trans4"]
            },
            "nouns": {
                "nouns1": ["trans1", "trans2", "trans3"]
            },
            "adjectives" {
                "adjective1": ["trans1", "trans2"]
            }
        },
        "match": 1.0
    }

Main classes
------------
.. autoclass:: google_translate.GoogleTranslator
    :members:

Other classes
-------------
.. autoclass:: google_translate.UserAgentSelector
    :members:

.. autoclass:: google_translate.ProxySelector
    :members:

.. autoclass:: google_translate.cache.Cache
    :members:

.. rubric:: Footnotes
.. [#f1] <https://techblog.willshouse.com/2012/01/03/most-common-user-agents/>
