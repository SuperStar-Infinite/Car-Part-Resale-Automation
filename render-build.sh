#!/usr/bin/env bash
set -e

STORAGE_DIR=/opt/render/project/.render

if [[ ! -d "$STORAGE_DIR/chrome" ]]; then
  echo "...Downloading Chrome"
  mkdir -p "$STORAGE_DIR/chrome"
  cd "$STORAGE_DIR/chrome"
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x google-chrome-stable_current_amd64.deb "$STORAGE_DIR/chrome"
  cd - >/dev/null
else
  echo "...Chrome already installed"
fi

echo "...Installing Python deps"
pip install --upgrade pip
pip install -r requirements.txt
