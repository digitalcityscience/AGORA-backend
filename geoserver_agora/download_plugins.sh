#!/usr/bin/env bash
set -euo pipefail

# USAGE: ./download_plugins.sh GEOSERVER_VERSION PLUGINS
# EXAMPLE: ./download_plugins.sh "2.27.6" "mbstyle vectortiles"
GEOSERVER_VERSION=${1:?GeoServer version is required}
PLUGINS=${2:?At least one plugin is required}

echo "GEOSERVER_VERSION: $GEOSERVER_VERSION"
echo "PLUGINS: $PLUGINS"

# clean plugins folder
echo "clean up old plugins in ./plugins/"
mkdir -p ./plugins
find ./plugins -mindepth 1 ! -name '.keep' -exec rm -rf {} +

for plugin in $PLUGINS; do
  echo "fetching data for $plugin"
  archive="geoserver-$GEOSERVER_VERSION-$plugin-plugin.zip"
  url="https://downloads.sourceforge.net/project/geoserver/GeoServer/$GEOSERVER_VERSION/extensions/$archive"

  if command -v curl >/dev/null 2>&1; then
    curl --fail --location --output "$archive" "$url"
  elif command -v wget >/dev/null 2>&1; then
    wget --output-document "$archive" "$url"
  else
    echo "curl or wget is required" >&2
    exit 1
  fi

  unzip -o "$archive" -d ./plugins
  rm "$archive"
done
printf "......\n\nfinished downloading plugins\n"
