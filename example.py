#!/usr/bin/env ng ng-jython

from sys import exit, argv, path as syspath
from os.path import basename, isdir, splitext, join as pathjoin
from os import getcwd
syspath.append(pathjoin(getcwd(), '..', '..', 'text-tools', 'epubtool'))
from epubtool import EPUBTool
from glob import glob

class OWNEpub(EPUBTool):
    def __init__(self, srcdir, target, cover):
#        super(OWNEpub, self).__init__(srcdir, target, cover)
        EPUBTool.__init__(self, srcdir, target, cover)
        self._manifest=[]
        self._ritems = []
        self._toc = [] 
        self._collect_items(self.fullpath('OEBPS'))

    def _collect_items(self, path, subcomp=''):
        for F in glob(pathjoin(path, '*')):
            if isdir(F):
               self._collect_items(F, basename(F))
               continue

            if basename(F) in ['toc.ncx', 'content.opf']:
                """Already present:"""
#                    manifest+='''\
#<item id="ncx" href="toc.ncx"
#   media-type="application/x-dtbncx+xml" />
#'''                
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

    def gen_spine(self):
        spine="<itemref idref=\"cover\" />\n"
        for item in self._ritems:
            spine+='''\
<itemref idref="item%d" />
'''%(item,)
        return spine

    def gen_navmap(self):
        navmap=''
        play_order=1
        for document in self._toc:
            navmap+='''\
<navPoint id="ch%d" playOrder="%d">
  <navLabel>
<text>Chapter title</text>
  </navLabel>
  <content src="%s" />
</navPoint>
''' % (play_order,play_order, document)
            play_order+=1
        return navmap

srcdir = 'example'
target = 'example.epub'
E = OWNEpub(srcdir, target, 'cover')
E.write_epub(overwrite=True)
E.validate()
exit(0)
