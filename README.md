# EPUBTool

A simple-minded Jython class to aid hand-converting a collection of HTML files
into a valid EPUB document.

Some virtual methods provided, to allow customization of generated content.

The tool requires Adobe [epubcheck](https://github.com/IDPF/epubcheck)
(see example below).

## Prerequisites
* A set of HTML files
* Write a short script (around 100 lines) to subclass the EPUBTool with a content
processor and manifest generator. You can optionally provide a cover page and 
a ToC JSON file of the format:
```
[[html_file, nesting_level, entry_text], ... ]
```
Or, alternatively, generate one from a CHM *.hhc file using the script provided.
* For the exquisite results, you can also write an image file filter, pack
processor or even invoke HTML to XHTML content convertor!
* NB: you could individually suppress specific validation messages, or even
silence them altogether (see the launcher script).
* Run the launcher script.
* Voilla, you've got the EPUB book!


## Usage

Would recommend to run it from under the
[NailGun](http://martiansoftware.com/nailgun) Java framework to greatly speed
up iterative tasks.

The module is intended to be imported from some other Jython script as a class.
See the module file for the class details and usage example.

For example, the NailGun startup script could contain the following: 
```
...
EPUBCHECK=some_root/text-tools/epubcheck-4.0.2
CLASSPATH="${EPUBCHECK}/lib/*:${EPUBCHECK}/*:${CLASSPATH}"
export CLASSPATH
nohup java com.martiansoftware.nailgun.NGServer &
sleep 2
# Set up aliases
ng ng-alias ng-epubcheck com.adobe.epubcheck.tool.Checker
ng ng-alias ng-jython org.python.util.jython
...
```

You can then run the tool as follows:
```
ng-jython epubtool.py example example.epub
```

