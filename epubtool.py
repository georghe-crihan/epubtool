#!/usr/bin/env jython
from exceptions import NotImplementedError
from os.path import exists, isdir, basename, join as pathjoin 
from os import mkdir, getcwd
from glob import glob
# The library is in the epubcheck's classpath already.
from org.apache.commons.compress.archivers import ArchiveException, ArchiveOutputStream, ArchiveStreamFactory
from org.apache.commons.compress.archivers.zip import ZipArchiveEntry
from org.apache.commons.compress.utils import IOUtils
from java.util.zip import Deflater
from java.io import File, FileInputStream, BufferedInputStream, FileOutputStream
from com.adobe.epubcheck.api import EpubCheck

__all__ = ['EPUBTool']

class EPUBTool(object):
    """Simple-minded Jython class to aid hand-converting a collection of HTML
       files into a valid EPUB document."""
    def __init__(self, path, target, covername=None):
        self._path = path
        if not exists(path):
            mkdir(path)
        self._target = target
        self.epub = File(pathjoin(getcwd(), self._target))
        self._covername = covername

    def fullpath(self, name1, name2=None):
	# Don't want to bother with kwargs for now...
        if name2:
            return pathjoin(self._path, name1, name2)
        else:
            return pathjoin(self._path, name1)

    def _put_mimetype(self, overwrite=False):
        if overwrite or not exists(self.fullpath('mimetype')):
            F=open(self.fullpath('mimetype'), "w")
            F.write("application/epub+zip")
            F.close()

    def _put_metainf(self, overwrite=False):
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
        if overwrite or not exists(self.fullpath('META-INF', 'container.xml')):
            F=open(self.fullpath('META-INF', 'container.xml'), "w")
            F.write(container_xml)
            F.close()

    def _put_oebps(self):
        if not exists(self.fullpath('OEBPS')):
            mkdir(self.fullpath('OEBPS'))

    def gen_navmap(self):
        raise NotImplementedError('Pure virtual method gen_navmap.')

    def _put_tocncx(self, overwrite=False):
        if overwrite or not exists(self.fullpath('OEBPS','toc.ncx')):
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

    def gen_guide(self):
        raise NotImplementedError('Pure virtual method gen_guide.')

    def _put_contentopf(self, overwrite=False):
        if overwrite or not exists(self.fullpath('OEBPS','content.opf')):
            if self._covername:
                cover='''\
   <meta name="%s" content="cover-image"/>\
''' % (self._covername,)
            else:
                cover=''

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
   %s
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
''' % (self._target,cover) + self.gen_manifest() + '''\
</manifest>

<spine toc="ncx">
<!--
<itemref idref="item1" />
<itemref idref="item2" />
-->
''' + self.gen_spine() + '''\
</spine>

<guide>
''' + self.gen_guide() + '''\
</guide>
</package>
'''
            F=open(self.fullpath('OEBPS', 'content.opf'), "w")
            F.write(content_opf)
            F.close()

    def write(self, archive, path, dest):
        archive.putArchiveEntry(ZipArchiveEntry(dest))

        input = BufferedInputStream(FileInputStream(path))

        IOUtils.copy(input, archive)
        input.close()
        archive.closeArchiveEntry()

    def recursive_pack(self, Z, path, subcomp=''):
        """Recursive subdirectory packer.
           Should be faster than spawning zip from under JVM."""
        for F in glob(pathjoin(path, '*')):
            if isdir(F):
                self.recursive_pack(Z, F, pathjoin(subcomp, basename(F)))
                continue
            self.write(Z, F, pathjoin('OEBPS', subcomp, basename(F)))

    def write_epub(self, overwrite=False):
        self._put_mimetype(overwrite)
        self._put_metainf(overwrite)
        self._put_oebps()
        self._put_tocncx(overwrite)
        self._put_contentopf(overwrite)

        archiveStream = FileOutputStream(self.epub)
        archive = ArchiveStreamFactory().createArchiveOutputStream(ArchiveStreamFactory.ZIP, archiveStream)
        archive.setLevel(Deflater.NO_COMPRESSION)
        self.write(archive, self.fullpath('mimetype'), 'mimetype')
        archive.setLevel(Deflater.DEFLATED)
        self.write(archive, self.fullpath('META-INF', 'container.xml'), 'META-INF/container.xml')
        self.recursive_pack(archive, self.fullpath('OEBPS'))
        archive.finish();
        archiveStream.close()

    def validate(self):
        # Details here: https://github.com/IDPF/epubcheck/wiki/Library
        epubcheck = EpubCheck(self.epub)
        # Boolean
        return epubcheck.validate()





if __name__=='__main__':
    from sys import exit, argv

    class OWNEpub(EPUBTool):
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
