#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# Activate the shared uv-managed Python environment for the whole toolchain.
source "$(dirname "$(readlink -f "$0")")/../galenv" || exit 1

# Run the compiler directly using the Runtime.main function
python -c "import sys; sys.path.append('$HOME/.gal3'); from Runtime import Runtime; Runtime.main(['gal_main.txt', 'new_file.gal'])"