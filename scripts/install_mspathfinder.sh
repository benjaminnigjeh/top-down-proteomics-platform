#!/usr/bin/env bash
# Install MSPathFinderT (Informed Proteomics) on Linux
# Source: https://github.com/PNNL-Comp-Mass-Spec/Informed-Proteomics
# License: Apache 2.0
# Requires: .NET 6+ runtime

set -euo pipefail

VERSION="${MSPATHFINDER_VERSION:-1.1.8064}"
INSTALL_DIR="${INSTALL_DIR:-/opt/informed-proteomics}"

echo "Installing MSPathFinderT v${VERSION}..."

# Check for .NET runtime
if ! command -v dotnet &>/dev/null; then
    echo "Installing .NET 6 runtime..."
    if command -v apt-get &>/dev/null; then
        apt-get install -y dotnet-runtime-6.0 || \
        (curl -sSL https://dot.net/v1/dotnet-install.sh | bash /dev/stdin --channel 6.0 --runtime dotnet)
    else
        echo "Please install .NET 6 runtime manually: https://dotnet.microsoft.com/download"
        exit 1
    fi
fi

mkdir -p "$INSTALL_DIR"
TMPFILE=$(mktemp /tmp/mspathfinder-XXXX.zip)

URL="https://github.com/PNNL-Comp-Mass-Spec/Informed-Proteomics/releases/download/v${VERSION}/InformedProteomics.zip"
echo "Downloading from $URL..."
curl -fsSL "$URL" -o "$TMPFILE"

echo "Extracting to $INSTALL_DIR..."
unzip -q "$TMPFILE" -d "$INSTALL_DIR"
rm -f "$TMPFILE"

# Create wrapper script
cat > /usr/local/bin/MSPathFinderT <<'EOF'
#!/bin/bash
dotnet /opt/informed-proteomics/MSPathFinderT.dll "$@"
EOF
chmod +x /usr/local/bin/MSPathFinderT

echo ""
echo "MSPathFinderT installed. Verify:"
echo "  MSPathFinderT -version"
echo ""
echo "Update your .env:"
echo "  MSPATHFINDER_BIN=MSPathFinderT"
