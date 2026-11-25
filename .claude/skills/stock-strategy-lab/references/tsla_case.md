# Worked example: TSLA, 2010-06-29 .. 2026-11-23 (the run this skill was distilled from)

Full write-up and code: `Research/TeslaStrategy/` in this repository; LEAN algorithm:
`Algorithm.Python/TeslaTrendRegimeEarningsAlgorithm.py` (= assets/reference_lean_algorithm_tsla.py).

## Timeline and cost
(Numbering of the skill's phases.) Classic sweep (6,176 configs) -> reference A+B. Fase 1 workflow (harness audit +
data agent, ~30 min, 2 agents) -> 5 harness bugs fixed, 1 bad data row repaired, QQQ/SPY/VIX/IV/earnings/deliveries/opex
data. Fase 2 (7 families x (research + validator) = 14 agents, ~85 min with 2 concurrent agents, ~2.8M subagent tokens,
3,401 configs). Fase 3: lead combination (~15 min) + panel (optimizer + 3 skeptics, ~32 min, ~0.9M tokens). Fase 4 LEAN
(toolchain ~10 min, runs ~3-5 min each). Fase 5 review (code review + claims check, ~27 min, ~0.5M tokens). Total
wall-clock ~5-6 hours.

## Outcome
| Strategy | Sharpe IS / OOS / 2023+ | CAGR all | MDD |
|---|---|---|---|
| Buy & hold | 0.86 / 0.89 / 0.80 | 39.9% | -74% |
| Reference A+B (study 1) | 0.93 / 1.26 / 1.05 | 25.5% | -28% |
| Final F3 = min(1, .5*A*G + .5*B + .5*P) | 1.18 / 1.56 / 1.53 | 36.9% | -23% |
A = TSLA SMA10>SMA30; G = QQQ SMA10>SMA30; B = close <= 0.88 x close 5 sessions earlier, hold 3; P = earnings reaction
close >= +3% vs last pre-release close, hold 10. Per-trade averages: A*G +9.6% (83), B +2.55% (83), P +10.85% (24).
Panel's forward expectation: Sharpe ~0.9-1.05, 15-25%/yr, drawdowns -25% to -40%.

## Family verdicts (what generalises as a prior, not as a rule)
- Confirmed: post-earnings continuation after a strong positive reaction (asymmetric: negative reactions do not revert).
- Weak but robust: market-trend gate on the stock's trend module (crash insurance; helps when the stock is highly
  correlated with the index).
- Weak/fragile: VIX percentile gate, VIX panic trigger, volume-spike and 52-week-high modules, trend-strength sizing,
  all ML overlays (walk-forward ML did not beat simple rules).
- Refuted: implied-vol rank gate (too little data), volatility targeting (hurts a stock whose best days are volatile).
- Study 1: shorts lose on a strong stock; classic mean reversion decays; trend following halves drawdowns at similar
  Sharpe; picking last year's winner each year underperforms.
