#!/usr/bin/env bash
# Install TopPIC Suite (TopFD + TopPIC + TopMG) on Linux/macOS
# Source: https://github.com/toppic-suite/toppic-suite/releases
# License: MIT

set -euo pipefail

TOPPIC_VERSION="${TOPPIC_VERSION:-1.7.3}"
INSTALL_DIR="${INSTALL_DIR:-/opt/toppic-suite}"
ARCH=$(uname -m)
OS=$(uname -s)

echo "Installing TopPIC Suite v${TOPPIC_VERSION} on ${OS}/${ARCH}..."

if [[ "$OS" == "Linux" ]]; then
    URL="https://github.com/toppic-suite/toppic-suite/releases/download/v${TOPPIC_VERSION}/toppic-suite-${TOPPIC_VERSION}-linux.zip"
elif [[ "$OS" == "Darwin" ]]; then
    URL="https://github.com/toppic-suite/toppic-suite/releases/download/v${TOPPIC_VERSION}/toppic-suite-${TOPPIC_VERSION}-mac.zip"
else
    echo "Unsupported OS: $OS. Install manually from:"
    echo "  https://github.com/toppic-suite/toppic-suite/releases"
    exit 1
fi

mkdir -p "$INSTALL_DIR"
TMPFILE=$(mktemp /tmp/toppic-XXXX.zip)

echo "Downloading from $URL..."
curl -fsSL "$URL" -o "$TMPFILE"

echo "Extracting to $INSTALL_DIR..."
unzip -q "$TMPFILE" -d "$INSTALL_DIR"
rm -f "$TMPFILE"

# Find and symlink binaries
BIN_DIR=$(find "$INSTALL_DIR" -name topfd -type f | head -1 | xargs dirname)
if [[ -z "$BIN_DIR" ]]; then
    echo "ERROR: topfd binary not found in extracted archive."
    exit 1
fi

mkdir -p /usr/local/bin
for binary in topfd toppic topmg toplib; do
    if [[ -f "$BIN_DIR/$binary" ]]; then
        ln -sf "$BIN_DIR/$binary" /usr/local/bin/$binary
        chmod +x "$BIN_DIR/$binary"
        echo "  ✓ Linked: $binary -> /usr/local/bin/$binary"
    fi
done

echo ""
echo "TopPIC Suite installed. Verify:"
echo "  topfd --version"
echo "  toppic --version"
echo ""
echo "Update your .env:"
echo "  TOPFD_BIN=topfd"
echo "  TOPPIC_BIN=toppic"
