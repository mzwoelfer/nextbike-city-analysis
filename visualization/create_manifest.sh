#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/data"
echo "[" > manifest.json
for file in *.csv.gz; do
    if [ "$file" != "manifest.json" ]; then
        echo "\"$file\"," >> manifest.json
    fi
done
sed -i '$ s/,$//' manifest.json
echo "]" >> manifest.json
