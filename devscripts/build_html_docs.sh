#!/bin/bash

DOCS="../docs"
BUILD_DIR="_build/html"

echo "Building html docs..."
echo "Changing directory to $DOCS"
cd $DOCS

make clean
make html

echo "Applying patch to 'api.html'..."
patch _build/html/api.html < _patch/patch.diff

read -p "Open docs on firefox? (y/n) " choice

if [[ $choice == 'y' || $choice == 'Y' ]]; then
    firefox "`pwd`/$BUILD_DIR/index.html"
fi

exit 0
