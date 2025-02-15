#!/bin/bash
# Run when updating data/
set -e

git checkout master
git pull origin master

git checkout gh-pages
git reset --hard master

echo "!data/" >> .gitignore
git add data/

git commit -m '[CI/CD] Update data for GitHub pages'
git push origin gh-pages

git checkout master
