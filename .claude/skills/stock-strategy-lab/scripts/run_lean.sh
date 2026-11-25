#!/bin/bash
# Run a LEAN backtest of a Python algorithm from the repo's Algorithm.Python folder.
# usage: run_lean.sh <lean_repo_dir> <work_dir> <AlgorithmClass> <logfile> [extra LEAN launcher args]
#   The algorithm file must be <lean_repo_dir>/Algorithm.Python/<AlgorithmClass>.py.
#   Data comes from <work_dir>/leandata, Python from <work_dir>/py311 (see setup_lean.sh).
#   Extra environment variables you export (e.g. STRAT_OUT, STRAT_SLIPPAGE) are visible to the algorithm.
# Prints LEAN's exit code; read the STATISTICS:: lines of the log for LEAN's own summary.
REPO=$(realpath "${1:?lean repo}"); WORK=$(realpath "${2:?work dir}"); CLS=${3:?class}; LOG=$(realpath -m "${4:?log file}"); shift 4
cd "$REPO/Launcher/bin/Debug" || exit 1
export PYTHONNET_PYDLL=/usr/lib/x86_64-linux-gnu/libpython3.11.so
export PYTHONHOME=/usr
export PYTHONPATH="$WORK/py311/lib/python3.11/site-packages:$REPO/Launcher/bin/Debug"
timeout 1800 dotnet QuantConnect.Lean.Launcher.dll --algorithm-type-name "$CLS" --algorithm-language Python \
  --algorithm-location "../../../Algorithm.Python/$CLS.py" --close-automatically true \
  --data-folder "$WORK/leandata/" "$@" > "$LOG" 2>&1
echo "exit $?"
grep -E "ERROR|STATISTICS:: (Total Orders|Compounding Annual Return|Drawdown |Sharpe Ratio|Total Fees)" "$LOG" | head -20
