#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pycallgraph import PyCallGraph
    from pycallgraph.output import GraphvizOutput
except ImportError as error:
    print error
    sys.exit(1)

import google_translate


def create_diagram(function, *args, **kwargs):
    with PyCallGraph(output=GraphvizOutput()):
        print "Creating diagram for: %s" % function
        print "args=%s kwargs=%s" % (args, kwargs)
        function(*args, **kwargs)


def main():
    translator = google_translate.GoogleTranslator()

    if "translate" in sys.argv:
        create_diagram(translator.translate, "test", "el")
    elif "detect" in sys.argv:
        create_diagram(translator.detect, "test")
    elif "romanize" in sys.argv:
        create_diagram(translator.romanize, "test")
    elif "exists" in sys.argv:
        create_diagram(translator.word_exists, "test")
    elif "info" in sys.argv:
        create_diagram(translator.get_info_dict, "test", "en")
    else:
        create_diagram(translator.translate, ["test1", "test2", "test3"], "el")


if __name__ == '__main__':
    main()
