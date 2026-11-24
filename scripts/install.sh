#!/usr/bin/env bash
# =============================================================================
# FILE PURPOSE:
# Standalone installation script for the SoftLookup-PVM runtime SDK.
# Extracts softlookup-pvm-sdk.tar.gz into /opt/softlookup-pvm and sets up
# the global executable symlink at /usr/local/bin/softlookup-python.
# Run on Linux or WSL2 with: `bash scripts/install.sh [path_to_tarball]`
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARBALL="${1:-${SCRIPT_DIR}/../softlookup-pvm-sdk.tar.gz}"

if [ ! -f "${TARBALL}" ]; then
    # Check alternate locations
    if [ -f "${HOME}/pvm-softlookup/softlookup-pvm-sdk.tar.gz" ]; then
        TARBALL="${HOME}/pvm-softlookup/softlookup-pvm-sdk.tar.gz"
    else
        echo "Error: softlookup-pvm-sdk.tar.gz not found at ${TARBALL}" >&2
        echo "Please provide the path to softlookup-pvm-sdk.tar.gz as an argument." >&2
        exit 1
    fi
fi

echo "=========================================================="
echo " Installing SoftLookup-PVM Runtime SDK"
echo " Tarball Source : ${TARBALL}"
echo " Target Prefix  : /opt/softlookup-pvm"
echo " Symlink Target : /usr/local/bin/softlookup-python"
echo "=========================================================="

sudo mkdir -p /opt
echo "Extracting archive to /opt..."
sudo tar -xzf "${TARBALL}" -C /opt

# Ensure standard binary symlinks inside /opt/softlookup-pvm/bin
if [ -f /opt/softlookup-pvm/bin/python3.16 ]; then
    sudo ln -sf /opt/softlookup-pvm/bin/python3.16 /opt/softlookup-pvm/bin/python3
    sudo ln -sf /opt/softlookup-pvm/bin/python3.16 /opt/softlookup-pvm/bin/python
fi

echo "Configuring global binary symlink..."
sudo mkdir -p /usr/local/bin
sudo ln -sf /opt/softlookup-pvm/bin/python3.16 /usr/local/bin/softlookup-python

echo "Verifying installation..."
/usr/local/bin/softlookup-python -c "import sys; print('SoftLookup-PVM successfully verified at:', sys.executable); print('Version:', sys.version)"

echo "=========================================================="
echo " SoftLookup-PVM successfully installed!"
echo " Use 'softlookup-python' to run your scripts with soft lookup."
echo "=========================================================="
