# Visualize Nextbike data

🚧 WORK IN PROGRESS

## Prerequisites

1. Run http-server locally:
```SHELL
cd visualization/
```

2. Populated `data/` folder
Each JSON-file contains trips per day.
See the format at the end of this README.

# Start http server
```SHELL
python3 -m http.server 8000
```

3. Visit `localhost:8000` in your browser

## Deployment on GitHub Pages
GitHub Pages does not support directory listing, but pre-generating a manifest reference to the files in the `visualization/data` directory.

Use the `create_manifest.json` file to create a `manifest.json` file inside the `visualization/data` directory, listing all data JSON files.
This allows your client-side code to work seamlessly on GitHub Pages.

This step is automated in the [workflow to publish to Github Pages](../.github/workflows/static.yml)

## Credits
Incorporation features and concepts from [Bikesharing Vis](https://github.com/technologiestiftung/bikesharing-vis) by [Technologiestiftung Berlin](https://github.com/technologiestiftung)