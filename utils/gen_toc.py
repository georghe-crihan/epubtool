#!/usr/bin/env ng ng-jython

# Extract titles from a set of pages into a ToC.JSON file.

from bs4 import BeautifulSoup
from glob import glob
from sys import argv
from os.path import join as pathjoin
from json import dumps

srcdir = argv[1] if len(argv) > 1 else 'sandbox/EPUBs/p/book/OEBPS'
toc = [] 
for F in glob(pathjoin(srcdir, '*.htm')):
    with open(F, "rb") as f: 
        doc = BeautifulSoup(f, "html5lib")
        for elem in doc.findAll('title'):
            title = elem.text 
        toc.append((basename(F), 0, elem.text))

dumps(toc)
