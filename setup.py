#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""google-translate package setup file."""

from setuptools import setup

from google_translate import (
    __version__,
    __license__
)


setup(
    version             = __version__,
    license             = __license__,
    name                = "doodle-translate",
    author_email        = "ytubedlg@gmail.com",
    author              = "Sotiris Papadopoulos",
    url                 = "https://github.com/MrS0m30n3/google-translate",
    description         = "Small Python library to translate text for free using the Google translate.",

    packages            = ["google_translate"],
    scripts             = ["bin/google-translate"],
    install_requires    = ["twodict", "mock"],

    package_data        = {
        "google_translate": ["data/languages"]
    },

    classifiers         = [
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],

    keywords            = "google translate language free"
)
