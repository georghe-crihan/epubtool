#!/bin/sh

# Fill-in Safari Bookshelf titles from internal markup.

for F in $( ls ${1}/*.html ); do
	awk '
/<!--SafTocEntry=".*"-->/ {
       if ( match($0, /<!--SafTocEntry=".*"-->/) ) {
           title = substr($0, RSTART, RLENGTH);
           sub(/<!--SafTocEntry="/, "", title);
           sub(/"-->/, "", title);
       }
       next;
}

/^<title><\/title>/ {
       printf("<title>%s<\/title>\n", title);
       next;
}

{ print; }
' < "${F}" > "${F}.new"
	mv "${F}.new" "${F}"
done
