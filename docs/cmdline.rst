Command line
============
google_translate module comes with a command line script for **Linux**.

Usage
-----
**google-translate [mode] [options] word(s)**

Options
-------
Run `google-translate --help` to see a list with available options.

Examples
--------

  Translate single word::

    google-translate -d el "hello world"

  Translate multiple words::

    google-translate -d el car dog cat sun

  Get additional translations in json format::

    google-translate --additional -d el -o json house

  Detect source language::

    google-translate -m detect car

  Use a proxy::

    google-translate -d russian --proxy "127.0.0.1:8080" hello

  Add extra HTTP headers::

    google-translate -d russian hello --header "User-Agent:yolo" --header "Message:from russia with love"

  Translate file::

    google-translate -d greek file://myfile.txt

.. note:: Currently the google-translate script supports only one file.
