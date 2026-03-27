#!/bin/bash
set -e

echo "🐍 Python version:"
python --version

echo "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "📥 Installing dependencies..."
pip install -r requirements.txt --no-cache-dir

echo "✅ Build complete!"