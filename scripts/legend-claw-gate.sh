#!/bin/bash
# Legend Claw quality gate — shell entry point.
# Handles all subprocess-dependent operations (external scanners, contract commands).
# Delegates pure-logic checks to legend-claw-quality-gate.py.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE_PY="$SCRIPT_DIR/legend-claw-quality-gate.py"

if [ ! -f "$GATE_PY" ]; then
    echo "Legend Claw gate: FAIL"
    echo "- missing $GATE_PY"
    exit 1
fi

# Forward to Python for pure-logic checks (no subprocess)
python3 "$GATE_PY" "$@"
