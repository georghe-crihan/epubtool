#!/usr/bin/env ng ng-jython

# Dumb parser for HHC files ripped from some anchient Microsoft CHM bundle.
# It lacks case neutrality, also changed order of elements will surely break it.

from bs4 import BeautifulSoup
from json import dumps

def parse_hhc(src, Trace=False):
        with open(src, "rb") as f: 
            doc = BeautifulSoup(f, "html5lib")
            l = [] 
            d = []
            head = ''
            hd = 0
            key = ''
            val = ''
            for o in doc.findAll('object'):
                if o['type'] == 'text/sitemap':
                    for param in o.findAll('param'):
                        if param['name'] == 'Local': key = param['value']
                        if param['name'] == 'Name':
                            """Calculate depth along the way"""
                            val = param['value']
                            path = '.'.join(reversed([p.name for p in param.parentGenerator() if p]))
                            depth = path.count('.')
                            if depth not in d: d.append(depth)
                            if Trace:
                                print "{:10}|{:60}|{:10}".format(param.name,param.attrs, path)
                    if key == '':
                        """Chapter header detected, save it."""
                        hd = depth
                        head = val
                    else:
                        if head != '':
                            l.append((key, hd, head))
                        l.append((key, depth, val))
                        head = ''
                        key = ''
                        val = ''

        # Remap depth
        d2 = sorted(d)
        return dumps([(t[0].lower(), d2.index(t[1]), t[2]) for t in l ])
