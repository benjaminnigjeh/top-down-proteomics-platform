#!/usr/bin/env bash
# Install FLASHDeconv via OpenMS conda package
# Source: https://github.com/OpenMS/OpenMS
# License: BSD 3-Clause

set -euo pipefail

echo "Installing FLASHDeconv (via OpenMS)..."

if command -v conda &>/dev/null; then
    echo "Installing via conda..."
    conda install -y -c conda-forge -c bioconda openms
elif command -v pip &>/dev/null; then
    echo "Installing pyopenms (Python bindings — limited tool access)..."
    pip install pyopenms
    echo "WARNING: pyopenms does not include FLASHDeconv CLI. Use conda for full installation."
else
    echo "Neither conda nor pip found."
    echo "Install OpenMS manually from: https://www.openms.de/downloads/"
fi

echo ""
echo "Verify installation:"
echo "  FLASHDeconv --help"
echo ""
echo "Update your .env:"
echo "  FLASHDECONV_BIN=FLASHDeconv"
