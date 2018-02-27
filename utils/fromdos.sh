#!/bin/sh

# Strip LF from HTML files.

for F in $( ls ${1}/*.html* ); do
        tr -d "\015" < "${F}" > "${F}.new"
	mv "${F}.new" "${F}"
done
