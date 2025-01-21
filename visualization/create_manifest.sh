#!/bin/bash
cd data
echo "[" > manifest.json
for file in *.json; do
    if [ "$file" != "manifest.json" ]; then
        echo "\"$file\"," >> manifest.json
    fi
done
sed -i '$ s/,$//' manifest.json
echo "]" >> manifest.json