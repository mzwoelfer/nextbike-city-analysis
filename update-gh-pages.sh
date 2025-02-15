#!/bin/bash
# Run when updating data/
set -e

git checkout master
git pull origin master

git checkout gh-pages
git reset --hard master

# Remove "data/" line if it exists
sed -i '/^data\//d' .gitignore  
echo "!data/" >> .gitignore

git add .gitignore
git commit -m 'Allow gh-pages branch to track data/ directory'

git add data/
git commit -m '[CI/CD] Update data for GitHub pages'
git push origin gh-pages

git checkout master
