#!/usr/bin/env jython
from exceptions import NotImplementedError
from os.path import exists, isdir, basename, join as pathjoin 
from os import mkdir
from re import compile, sub
from glob import glob
# The library is in the epubcheck's classpath already.
from org.apache.commons.compress.archivers import ArchiveException, ArchiveOutputStream, ArchiveStreamFactory
from org.apache.commons.compress.archivers.zip import ZipArchiveEntry
from org.apache.commons.compress.utils import IOUtils
from java.util.zip import Deflater
from java.io import File, FileInputStream, BufferedInputStream, FileOutputStream
from com.adobe.epubcheck.api import EpubCheck, MasterReport
from com.adobe.epubcheck.messages import MessageDictionary, Severity

__all__ = ['EPUBTool']

class Reporter(MasterReport):
    """Almost verbatim copy of DefaultReportImpl in Java.
       Ref: https://github.com/IDPF/epubcheck/blob/v4.0.2/src/main/java/com/adobe/epubcheck/util/DefaultReportImpl.java"""
    def __init__(self, ePubName, info='', quiet=False, suppress=None):
        self._quiet = quiet
        self._suppress_count = 0
        self._suppress = suppress
        self._ePubName = ePubName
        self._msgdict = MessageDictionary(None, self)
        self._re_spaces = compile("[\s]+")
        self._supp_hashes = [ hash(msg) for msg in self._suppress ] if self._suppress else None

    def _fixMessage(self, message):
        if not message:
            return ""
        return self._re_spaces.sub(" ", message)

    def message(self, message_id, location, args):
        if (self._quiet):
           return

        # Somehow this is not arriving directly as in Java, but through MessageId...
        message = self._msgdict.getMessage(message_id)

        if message.getSeverity() in [Severity.SUPPRESSED, Severity.USAGE] or \
           (self._suppress and len(args) > 0 and hash(args[0]) in self._supp_hashes):
            self._suppress_count += 1
            return
        text = self._format_message(message, location, args)
        print text

    def _format_message(self, message, location, args):
        # FIXME: maybe fix the fileName sometime, to match the default reporter
        epubFileName = basename(self._ePubName)
        fileName = basename(location.getPath())
        # remove duplicate epub name from path and empty fileName variable
        fileName = "" if epubFileName.endswith(fileName) else "/" + fileName
        return "%s(%s): %s%s(%s,%s): %s" % ( \
        message.getSeverity(), \
        message.getID(), \
        epubFileName, \
        fileName, \
        location.getLine(), \
        location.getColumn(), \
        self._fixMessage(message.getMessage(args) if args != None and len(args) > 0 else message.getMessage()))

    def info(self, resource, feature, value):
        pass

    def initialize(self):
        pass

    def generate(self):
        return 0

    def get_suppress_count(self):
        return self._suppress_count


class EPUBTool(object):
    """Simple-minded Jython class to aid hand-converting a collection of HTML
       files into a valid EPUB document."""
    def __init__(self, path, target, covername=None):
        self._path = path
        if not exists(path):
            mkdir(path)
        self._target = target
        self.epub = File(self._target)
        self._covername = covername
        self._reporter = None

    def fullpath(self, *args):
        p = self._path
        for a in args:
            p = pathjoin(p, a)
        return p

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
''' % (basename(self._target),cover) + self.gen_manifest() + '''\
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

    def indent(self, pos, text):
        spc = ' ' * pos
        t = []
        for line in text.splitlines():
            t.append(spc + line)
        return '\n'.join(t)

    def _put_nav_entry(self, ind, play_order, text, f):
        return self.indent((ind + 1) * 4 , '''
<navPoint id="ch%d" playOrder="%d">
  <navLabel>
    <text>%s</text>
  </navLabel>
  <content src="%s" />
''' % (play_order,play_order,text,f)
        )

    def _close_nav_entry(self, indent):
        return self.indent((indent + 1) * 4, '''
</navPoint>'''
        )


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

    def validate(self, quiet=False, suppress=None):
        # Details here: https://github.com/IDPF/epubcheck/wiki/Library
        self._reporter = Reporter(self._target, quiet=quiet, suppress=suppress)
        epubcheck = EpubCheck(self.epub, self._reporter) 
        # Boolean
        return epubcheck.validate()

    def get_suppress_count(self):
        return self._reporter.get_suppress_count()





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
