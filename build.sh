#!/bin/bash
set -e
pip install --upgrade pip wheel
pip install -r requirements.txt --prefer-binary --no-cache-dir
echo "✅ Build complete!"
