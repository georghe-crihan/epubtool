# EPUBTool

A simple-minded Jython class to aid hand-converting a collection of HTML files
into a valid EPUB document.

Some virtual methods provided, to allow customization of generated content.

Would recommend to run it from under the NailGun Java framework to greatly
speed up iterative tasks.

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

