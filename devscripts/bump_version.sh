#!/bin/bash

# Script to bump the version and update the README.md & docs/*
# Last-Revision: 2016-12-09
#
# Usage: ./bump_version.sh <new-version>

FILES=`cat <<EOF
google_translate/version.py
README.md
docs/intro.rst
docs/conf.py
EOF`


function update_version {
    echo "Updating file: $3"
    sed -i "s/$1/$2/g" $3
}


if [ $# -ne 1 ]; then
    echo "Usage: ./bump_version.sh <new-version>"
    exit 1
fi


cd ..

new_version=$1
cur_version=$(grep "version" "google_translate/version.py" | cut -d " " -f 3 | tr -d "'")

echo "Current version = $cur_version"
echo "New version     = $new_version"
echo

for file in $FILES; do
    update_version $cur_version $new_version $file
done


cd "devscripts"

read -p "Rebuild HTML docs? (y/n) " choice

if [[ $choice == 'y' || $choice == 'Y' ]]; then
    ./build_html_docs.sh
fi

echo "Done"
exit 0
