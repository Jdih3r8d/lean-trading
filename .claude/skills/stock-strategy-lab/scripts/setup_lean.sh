#!/bin/bash
# One-time LEAN toolchain setup in a fresh Ubuntu 24.04 cloud container (what worked in the TSLA study).
# usage: setup_lean.sh <lean_repo_dir> <work_dir>
#   - installs the .NET 10 SDK from the Ubuntu archive (builds.dotnet.microsoft.com is usually blocked by the proxy,
#     archive.ubuntu.com and api.nuget.org are reachable)
#   - builds the LEAN solution (~4 min, thousands of analyzer warnings are normal, 0 errors expected)
#   - creates a Python 3.11 venv with pandas/numpy for LEAN's pythonnet (LEAN needs 3.11; the system python3 is 3.13)
#   - creates <work_dir>/leandata with market-hours, symbol-properties and the interest-rate file copied from the repo
#     (add your tickers with to_lean_data.py; keep custom data OUT of the repo's tracked Data/ folder)
set -euo pipefail
REPO=${1:?lean repo}; WORK=${2:?work dir}
mkdir -p "$WORK"
if ! command -v dotnet >/dev/null || ! dotnet --list-sdks | grep -q '^10\.'; then
  apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq dotnet-sdk-10.0
fi
dotnet --list-sdks
(cd "$REPO" && dotnet build QuantConnect.Lean.sln -c Debug -v q -nologo 2>&1 | tail -3)
if [ ! -x "$WORK/py311/bin/python" ]; then
  python3.11 -m venv "$WORK/py311"
  "$WORK/py311/bin/python" -m pip install -q "pandas<3" "numpy<2.3"
fi
"$WORK/py311/bin/python" -c "import pandas, numpy; print('py311 pandas', pandas.__version__)"
mkdir -p "$WORK/leandata/alternative/interest-rate/usa"
cp -r "$REPO/Data/market-hours" "$REPO/Data/symbol-properties" "$WORK/leandata/"
cp "$REPO/Data/alternative/interest-rate/usa/interest-rate.csv" "$WORK/leandata/alternative/interest-rate/usa/"
echo "LEAN ready. Data folder: $WORK/leandata ; venv: $WORK/py311"
