#!/bin/bash
# Create a strategy lab for one stock.
# usage: new_lab.sh <TICKER> <lab_dir> [is_end YYYY-MM-DD] [rec_start YYYY-MM-DD]
# The lab gets the audited harness/engine, the protocol and a config.json with the evaluation periods.
# Put the stock's daily split-adjusted OHLCV in <lab_dir>/data/main.csv (date,open,high,low,close,volume);
# is_start is filled in automatically from main.csv the first time harness_check runs (see SKILL.md).
set -euo pipefail
TICKER=${1:?ticker}; LAB=${2:?lab dir}; IS_END=${3:-}; REC_START=${4:-}
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL="$(dirname "$HERE")"
mkdir -p "$LAB/data"
cp "$HERE/harness.py" "$HERE/engine.py" "$LAB/"
cp "$SKILL/references/protocol.md" "$LAB/PROTOCOL.md"
YEAR=$(date +%Y)
python3 - "$LAB" "$TICKER" "$IS_END" "$REC_START" "$YEAR" <<'EOF'
import json, os, sys
lab, ticker, is_end, rec_start, year = sys.argv[1:6]
year = int(year)
cfg_path = os.path.join(lab, 'config.json')
cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {}
cfg.update({'ticker': ticker.upper(), 'ytd_year': year})
cfg.setdefault('is_start', '1990-01-01')
if is_end:
    cfg['is_end'] = is_end
if rec_start:
    cfg['rec_start'] = rec_start
cfg.setdefault('rec_start', f'{year - 3}-01-01')
cfg.setdefault('is_end', f'{year - 8}-12-31')
y = int(cfg['is_end'][:4])
cfg['oos_start'] = f'{y + 1}-01-01'
json.dump(cfg, open(cfg_path, 'w'), indent=1)
print(json.dumps(cfg, indent=1))
EOF
echo "lab ready: $LAB  (next: put data/main.csv, then python3 $HERE/check_data.py $LAB)"
