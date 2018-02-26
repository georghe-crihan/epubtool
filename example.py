#!/usr/bin/env ng ng-jython

from glob import glob
from os.path import basename, exists, isdir, splitext, join as pathjoin
from epubtool import EPUBTool

class OWNEpub(EPUBTool):
    def __init__(self, srcdir, target, cover=None):
        super(OWNEpub, self).__init__(srcdir, target, cover)
        self._manifest = []
        self._ritems = []
        self._spine = []
        self._toc = []
        self._images = []
        self._filter_images(self.fullpath('OEBPS', 'img')) 

    def _filter_images(self, path):
        """Filter-out extra low-res images."""
        for I in glob(pathjoin(path, '*')):
            filename, ext = splitext(I)
            if exists(filename + 'x' + '.gif') or \
               exists(filename + 'x' + '.GIF') or \
               exists(filename + 'x' + '.jpg') or \
               exists(filename + 'x' + '.JPG'):
                continue

            self._images.append(basename(I))

    def recursive_pack(self, Z, path, subcomp=''):
        if subcomp=='img':
            """Handle images separately."""
            for F in self._images:
                self.write(Z, pathjoin(path, F), pathjoin('OEBPS', subcomp, F))
        else:
            EPUBTool.recursive_pack(self, Z, path, subcomp)

    def process_content(self, path, subcomp=''):
        # Sorted index there
        items = glob(pathjoin(path, '*'))
        spine = []
        for i in self._spine:
            pj = pathjoin(path, i)
            if pj in items: items.remove(pj)
            spine.append(pj)

        for F in spine + items:
            if isdir(F):
               self.process_content(F, basename(F))
               continue

            if basename(F) in ['toc.ncx', 'content.opf']:
                """Already present:"""
#                    manifest+='''\
#<item id="ncx" href="toc.ncx"
#   media-type="application/x-dtbncx+xml" />
#'''                
                continue

            if subcomp=='img' and basename(F) not in self._images:
                """Filter-out the extra low-res images."""
                continue

            filename, ext = splitext(F)
            if ext in ['.htm', '.html']:
                mime_type='application/xhtml+xml'
                self._ritems.append(len(self._manifest)+1)
                self._toc.append(basename(F))
            elif ext in ['.css']:
                mime_type='text/css'
            elif ext in ['.jpg', '.jpeg', '.JPG']:
                mime_type='image/jpeg'
            elif ext in ['.gif', '.GIF']:
                mime_type='image/gif'
            else:
                mime_type=''

            self._manifest.append((pathjoin(subcomp, basename(F)), mime_type))

    def gen_manifest(self):
        manifest=''
        nitem = 1
        for item in self._manifest:
            if item[0]=='img/cover.jpeg':
                manifest+='''\
<item id="cover" href="%s"
   media-type="%s" />
''' % (item[0],item[1])

        for item in self._manifest:
            if item[0]=='img/cover.jpeg':
                continue
            manifest+='''\
<item id="item%d" href="%s"
   media-type="%s" />
''' % (nitem,item[0],item[1])
            nitem+=1
        return manifest

    def gen_guide(self):
        return '''\
<reference href="cover.htm" type="cover" title="Cover" />
'''
#<reference href="cover.htm" type="text" title="Cover" />

