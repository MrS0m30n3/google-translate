Contribute
==========

.. warning:: On Python 2.* you need to install the mock module.

To run the tests::

    python -m unittest discover

To run **all** the tests::

    python -m unittest discover -cc

To build the html documentation::

    cd devscripts/
    ./build_html_docs.sh

To create the call diagram::

    cd devscripts/
    ./create_call_trace.py { | translate | detect | romanize | exists | info}


Report an issue
---------------
    To report an issue go to: `link <https://github.com/MrS0m30n3/google-translate/issues>`_

.. note:: Please before reporting an issue check to see if it is already solved-exists.

Send a pull request
-------------------
    1. Fork the repository
    2. Write a test that solves the problem and make sure that the test fails
    3. Write code to make the test pass
    4. Run all the tests to make sure nothing is broken
    5. Add yourself to the AUTHORS file
    6. Open a new pull request

Not sure how to help?
---------------------
    The `TODO <https://github.com/MrS0m30n3/google-translate/blob/master/TODO>`_ list is a good place to start.
