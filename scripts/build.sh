#!/usr/bin/env bash
# =============================================================================
# FILE PURPOSE:
# End-to-end build automation script that configures, compiles (via make -j),
# altinstalls into /opt/softlookup-pvm, and packages softlookup-pvm-sdk.tar.gz.
# Run on Linux or WSL2 with: `bash scripts/build.sh`
# =============================================================================

set -euo pipefail

CPYTHON_DIR="${1:-$HOME/pvm-softlookup/cpython-src}"
INSTALL_PREFIX="/opt/softlookup-pvm"
OUTPUT_DIR="${2:-$HOME/pvm-softlookup}"

echo "=========================================================="
echo " Building SoftLookup-PVM from source"
echo " Source Directory : ${CPYTHON_DIR}"
echo " Install Prefix   : ${INSTALL_PREFIX}"
echo " Package Dest     : ${OUTPUT_DIR}"
echo "=========================================================="

if [ ! -d "${CPYTHON_DIR}" ]; then
    echo "Error: Source directory '${CPYTHON_DIR}' not found." >&2
    exit 1
fi

cd "${CPYTHON_DIR}"

echo "Step 1: Configuring build..."
./configure --prefix="${INSTALL_PREFIX}" --disable-test-modules

echo "Step 2: Compiling runtime with $(nproc) cores..."
make -j"$(nproc)"

echo "Step 3: Installing into ${INSTALL_PREFIX}..."
sudo make altinstall

echo "Step 4: Packaging standalone SDK archive..."
mkdir -p "${OUTPUT_DIR}"
cd /opt
sudo tar -czf "${OUTPUT_DIR}/softlookup-pvm-sdk.tar.gz" softlookup-pvm

echo "=========================================================="
echo " Build & packaging complete!"
echo " Output archive: ${OUTPUT_DIR}/softlookup-pvm-sdk.tar.gz"
echo "=========================================================="
