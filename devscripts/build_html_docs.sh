#!/bin/bash

DOCS="../docs"
BUILD_DIR="_build/html"
DOCS_PUBLIC="docs/"
SITE="https://mrs0m30n3.github.io/google-translate/docs/"

if [[ $# -gt 1 ]]; then
    echo "Usage: $0 [clean]"
    exit 1
fi


echo "Building html docs..."
echo "Changing directory to $DOCS"
cd $DOCS

if [[ $1 == "clean" ]]; then
    make clean
fi

mkdir -p $DOCS_PUBLIC

make html

echo "Applying patch to 'api.html'..."
patch "$BUILD_DIR/api.html" < _patch/patch.diff

read -p "Open $BUILD_DIR/index.html on firefox? (y/n) " choice

if [[ $choice == 'y' || $choice == 'Y' ]]; then
    firefox "`pwd`/$BUILD_DIR/index.html" &
fi

read -p "Publish docs on Github pages? (y/n) " choice

if [[ $choice == 'y' || $choice == 'Y' ]]; then
    cp -v -u "$BUILD_DIR/"*.html "$DOCS_PUBLIC"
    cp -v -u "$BUILD_DIR/"*.js "$DOCS_PUBLIC"
    cp -R -v -u "$BUILD_DIR/_static" "$DOCS_PUBLIC"

    read -p "Commit changes? (y/n) " choice

    if [[ $choice == 'y' || $choice == 'Y' ]]; then
        git commit -a -m "Update doc html pages"
        echo "Now just run 'git push origin master' and fire-up a browser on: $SITE"
    fi
fi

exit 0
