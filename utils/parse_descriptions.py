#!/usr/bin/env ng ng-jython

# Parse descriptions ripped from some anchient Microsoft CHM bundle.

from bs4 import BeautifulSoup
from glob import glob
from sys import argv
from os.path import join as pathjoin

srcdir = argv[1] if len(argv) > 1 else 'andbox/EPUBs/p/descriptions'
for F in glob(pathjoin(srcdir, '*.htm')):
    with open(F, "rb") as f: 
        doc = BeautifulSoup(f, "html5lib")
        for elem in doc.findAll('title'):
            title = elem.text 
        for elem in doc.findAll('i'):
            caption = elem.text
        for elem in doc.findAll('img'):
            img = elem
        print "%s %s %s %s: %s" % (img['src'], img['width'], img['height'], title, caption)
