#!/usr/bin/env jython
from exceptions import NotImplementedError
from os.path import exists, join as pathjoin 
from os import mkdir, getcwd, chdir, sep
from subprocess import call 
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from com.adobe.epubcheck.api import EpubCheck
from java.io import File

class EPUBGen(object):
    """Simple-minded Jython class to aid hand-converting a collection of HTML
       files into a valid EPUB document."""
    def __init__(self, path, target):
        self._path = path
        if not exists(path):
            mkdir(path)
        self._target = target
        self._cwd = getcwd()

    def fullpath(self, name1, name2=None):
	# Don't want to mess with kwargs for now...
        if name2:
            return pathjoin(self._path, name1, name2)
        else:
            return pathjoin(self._path, name1)

    def _put_mimetype(self):
        F=open(self.fullpath('mimetype'), "w")
        F.write("application/epub+zip")
        F.close()

    def _put_metainf(self):
        if not exists(self.fullpath('META-INF')):
            mkdir(self.fullpath('META-INF'))
        container_xml = '''\
<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
   <rootfiles>
      <rootfile full-path="OEBPS/content.opf"
      media-type="application/oebps-package+xml"/>
   </rootfiles>
</container>
'''
        F=open(self.fullpath('META-INF', 'container.xml'), "w")
        F.write(container_xml)
        F.close() 

    def _put_oebps(self):
        if not exists(self.fullpath('OEBPS')):
            mkdir(self.fullpath('OEBPS'))

    def gen_navmap(self):
        raise NotImplementedError('Pure virtual method gen_navmap.')

    def _put_tocncx(self, overwrite=False):
        if overwrite or not exists(self.fullpath('toc.ncx')):
            toc_ncx='''\
<?xml version="1.0"?>
<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
  "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">

<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
   <head>
       <meta name="dtb:uid" content="RT8513Z9UM0NLKLF8QX9QDJ3E6ZFL2"/>
       <meta name="dtb:depth" content="3"/>
       <meta name="dtb:totalPageCount" content="0"/>
       <meta name="dtb:maxPageNumber" content="0"/>
   </head>
   <docTitle>
       <text>Book title</text>
   </docTitle>

<navMap>
<!--
<navPoint id="ch1" playOrder="1">
  <navLabel>
    <text>Chapter title</text>
  </navLabel>
  <content src="doc1.html" />
</navPoint>
-->
''' + self.gen_navmap() + '''\
</navMap>
</ncx>
'''
            F=open(self.fullpath('OEBPS', 'toc.ncx'), "w")
            F.write(toc_ncx)
            F.close()

    def gen_manifest(self):
        raise NotImplementedError('Pure virtual method gen_manifest.')

    def gen_spine(self):
        raise NotImplementedError('Pure virtual method gen_spine.')

    def _put_contentopf(self, overwrite=False):
        if overwrite or not exists(self.fullpath('conent.opf')):
            content_opf='''\
<?xml version="1.0"?>

<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="dcidid" version="2.0">

<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:dcterms="http://purl.org/dc/terms/"
   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
   xmlns:opf="http://www.idpf.org/2007/opf">
   <dc:title>Title here</dc:title>
   <dc:language xsi:type="dcterms:RFC3066">en</dc:language>
   <dc:identifier id="dcidid" opf:scheme="URI">
      %s 
      </dc:identifier>
   <dc:subject>A list of comma-separated keywords here
      </dc:subject>
   <dc:description>A description here.
      </dc:description>
   <dc:relation>http://www.example.com/</dc:relation>
   <dc:creator>John Doe</dc:creator>
   <dc:publisher>John Doe</dc:publisher>
   <dc:date xsi:type="dcterms:W3CDTF">2007-12-28</dc:date>
   <dc:date xsi:type="dcterms:W3CDTF">2010-08-27</dc:date>
   <dc:rights>Creative Commons BY-SA 3.0 License.</dc:rights>
</metadata>

<manifest>
<item id="ncx" href="toc.ncx"
   media-type="application/x-dtbncx+xml" />
<!--
<item id="item1" href="doc1.html"
   media-type="application/xhtml+xml" />
<item id="item3" href="style.css"
   media-type="text/css" />
-->
''' % (self._target,) + self.gen_manifest() + '''\
</manifest>

<spine toc="ncx">
<!--
<itemref idref="item1" />
<itemref idref="item2" />
-->
''' + self.gen_spine() + '''\
</spine>
</package>
'''
            F=open(self.fullpath('OEBPS', 'content.opf'), "w")
            F.write(content_opf)
            F.close()

    def write_epub(self, overwrite=False):
        self._put_mimetype()
        self._put_metainf()
        self._put_oebps()
        self._put_tocncx(overwrite)
        self._put_contentopf(overwrite)

        Z=ZipFile(self._target, 'w', ZIP_DEFLATED)
        Z.write(self.fullpath('mimetype'), 'mimetype', ZIP_STORED)
        Z.write(self.fullpath('META-INF', 'container.xml'), 'META-INF/container.xml')
        Z.close()
        chdir(self._path)
        call(['zip', '-r', pathjoin(self._cwd, self._target), 'OEBPS' + sep])
        chdir(self._cwd)

    def validate(self):
        # Details here: https://github.com/IDPF/epubcheck/wiki/Library
        epub = File(pathjoin(self._cwd, self._target))
        epubcheck = EpubCheck(epub)
        # Boolean
        return epubcheck.validate()





if __name__=='__main__':
    from sys import exit, argv

    class OWNEpub(EPUBGen):
        def gen_navmap(self):
            return ''

        def gen_manifest(self):
            return ''

        def gen_spine(self):
            return ''

    if len(argv) < 3:
        print "usage: %s <src-directory> <outfile.epub>" % (argv[0],)
        exit(1)

    srcdir = argv[1]
    target = argv[2]
    E = OWNEpub(srcdir, target)
    E.write_epub()
    E.validate()
    exit(0)
