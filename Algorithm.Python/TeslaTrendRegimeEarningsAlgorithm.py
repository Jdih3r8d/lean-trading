# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# TSLA trend / market-regime / earnings strategy ("F3" in Research/TeslaStrategy): w[t] = min(1, 0.5*A[t]*G[t] + 0.5*B[t] + 0.5*P[t]), decided on the close of t, traded at the open of t+1.
#   A: SMA10 > SMA30 of TSLA closes (split-adjusted).
#   G: SMA10 > SMA30 of QQQ closes (dividend-adjusted, total return).
#   B: close[t]/close[t-5]-1 <= -12% -> weight 1 on closes t, t+1, t+2 (buy open t+1, sell open t+4);
#      signals while holding and on the exit-decision close t+3 are ignored.
#   P: on an earnings reaction session R (first session whose OPEN reflects the release), if close[R]/close[R-1]-1 >= +3%
#      -> weight 1 on closes R..R+9 (buy open R+1, sell open R+11). R-1 is the last session that closed before the release.
#
# Implementation choices (see Research/TeslaStrategy/README.md):
#   * TSLA and QQQ are subscribed in RAW mode: orders, holdings and IBKR per-share fees use real share counts, and LEAN
#     applies splits to holdings and open orders. The signal windows are kept in adjusted terms by rescaling the stored
#     closes on every split (x split_factor) and every dividend (x (1 - distribution/reference_price)); this is exactly
#     the causal equivalent of the back-adjusted research files.
#   * fill_forward=False and an is_fill_forward guard: a fill-forwarded bar must never count as a session.
#   * Orders: market-on-open, sized with the decision close and the equity at that close; rebalance when the target
#     changes or the held weight drifts more than BAND (0.05) from the target.
#   * MODE 'close'  : decide in on_data on the daily bar (DailyPreciseEndTime -> 16:00 ET), MOO for the next open.
#     MODE 'morning': stateless; a scheduled event 30 min before the open rebuilds everything from SCALED_RAW daily
#                     history (70 bars) and sends the MOO. Recommended live: official closes, restart-safe, no order
#                     outstanding across a split, splits/dividends handled by the history scaling (SCALED_RAW = adjusted to the request date,
#                     i.e. continuous with the raw bars that follow; ADJUSTED would be scaled to the END of the factor
#                     file and breaks continuity with later raw bars in a backtest).
from AlgorithmImports import *
import os
import csv
from datetime import date, timedelta

# First session whose open reflects each quarterly results release (65 after the close, 2012-11-05 before the open).
# MUST be extended every quarter (Tesla announces the date ~2-3 weeks ahead); extra dates can be passed with the
# F3_EXTRA_REACTION_SESSIONS environment variable / 'extra_reaction_sessions' parameter (comma-separated YYYY-MM-DD).
REACTION_SESSIONS = [
    '2010-08-05', '2010-11-10', '2011-02-16', '2011-05-05', '2011-08-04', '2011-11-03',
    '2012-02-16', '2012-05-10', '2012-07-26', '2012-11-05', '2013-02-21', '2013-05-09',
    '2013-08-08', '2013-11-06', '2014-02-20', '2014-05-08', '2014-08-01', '2014-11-06',
    '2015-02-12', '2015-05-07', '2015-08-06', '2015-11-04', '2016-02-11', '2016-05-05',
    '2016-08-04', '2016-10-27', '2017-02-23', '2017-05-04', '2017-08-03', '2017-11-02',
    '2018-02-08', '2018-05-03', '2018-08-02', '2018-10-25', '2019-01-31', '2019-04-25',
    '2019-07-25', '2019-10-24', '2020-01-30', '2020-04-30', '2020-07-23', '2020-10-22',
    '2021-01-28', '2021-04-27', '2021-07-27', '2021-10-21', '2022-01-27', '2022-04-21',
    '2022-07-21', '2022-10-20', '2023-01-26', '2023-04-20', '2023-07-20', '2023-10-19',
    '2024-01-25', '2024-04-24', '2024-07-24', '2024-10-24', '2025-01-30', '2025-04-23',
    '2025-07-24', '2025-10-23', '2026-01-29', '2026-04-23', '2026-07-23', '2026-10-22',
]


class F3State:
    """Signal state, one step per TSLA session. Windows hold adjusted closes (most recent last)."""
    FAST, SLOW = 10, 30
    DROP_N, DROP_THR, DROP_HOLD = 5, -0.12, 3
    EARN_THR, EARN_HOLD = 0.03, 10

    def __init__(self, reaction):
        self.reaction = reaction
        self.tc, self.qc = [], []
        self.b_hold = self.b_cool = self.p_hold = self.p_cool = 0

    def rescale_tsla(self, f):
        self.tc = [x * f for x in self.tc]

    def rescale_qqq(self, f):
        self.qc = [x * f for x in self.qc]

    def add_qqq(self, close):
        self.qc = (self.qc + [close])[-self.SLOW:]

    def step(self, session, close):
        """Add the TSLA close of `session` (a date) and return (a, g, b, p, target) decided at that close.
        The QQQ close of the same session must already be in the QQQ window."""
        tc = (self.tc + [close])[-max(self.SLOW, self.DROP_N + 1):]
        self.tc = tc
        if len(tc) >= self.DROP_N + 1 and self.b_cool == 0 and tc[-1] / tc[-1 - self.DROP_N] - 1 <= self.DROP_THR:
            self.b_hold, self.b_cool = self.DROP_HOLD, self.DROP_HOLD + 1
        if session in self.reaction and len(tc) >= 2 and self.p_cool == 0 and tc[-1] / tc[-2] - 1 >= self.EARN_THR:
            self.p_hold, self.p_cool = self.EARN_HOLD, self.EARN_HOLD + 1
        b = 1.0 if self.b_hold > 0 else 0.0
        p = 1.0 if self.p_hold > 0 else 0.0
        a = 1.0 if len(tc) >= self.SLOW and sum(tc[-self.FAST:]) / self.FAST > sum(tc[-self.SLOW:]) / self.SLOW else 0.0
        qc = self.qc
        g = 1.0 if len(qc) >= self.SLOW and sum(qc[-self.FAST:]) / self.FAST > sum(qc[-self.SLOW:]) / self.SLOW else 0.0
        self.b_hold, self.b_cool = max(0, self.b_hold - 1), max(0, self.b_cool - 1)
        self.p_hold, self.p_cool = max(0, self.p_hold - 1), max(0, self.p_cool - 1)
        return a, g, b, p, min(1.0, 0.5 * a * g + 0.5 * b + 0.5 * p)


class TeslaTrendRegimeEarningsAlgorithm(QCAlgorithm):
    HISTORY_BARS = 70          # >= 30 for the SMAs; replaying >= 15 bars reproduces the B/P state exactly

    def _param(self, name, default):
        return os.environ.get('F3_' + name.upper(), self.get_parameter(name, default))

    def initialize(self):
        self.set_start_date(2010, 6, 29)
        self.set_end_date(2026, 11, 23)
        self.set_cash(float(self._param('cash', '100000')))
        self.set_brokerage_model(BrokerageName.INTERACTIVE_BROKERS_BROKERAGE, AccountType.MARGIN)
        self.settings.daily_precise_end_time = True
        self._band = float(self._param('band', '0.05'))
        self._mode = self._param('mode', 'close')
        self._out = self._param('out', '')
        self._tsla = self.add_equity('TSLA', Resolution.DAILY, fill_forward=False,
                                     data_normalization_mode=DataNormalizationMode.RAW).symbol
        self._qqq = self.add_equity('QQQ', Resolution.DAILY, fill_forward=False,
                                    data_normalization_mode=DataNormalizationMode.RAW).symbol
        self.set_benchmark(self._tsla)
        # optional per-side slippage on the MOO fill price (harness base cost = 5 bp per side; the auction pays no spread)
        self._slip = float(self._param('slippage', '0'))
        if self._slip > 0:
            self.securities[self._tsla].set_slippage_model(ConstantSlippageModel(self._slip))
        extra = [d for d in self._param('extra_reaction_sessions', '').split(',') if d.strip()]
        self._reaction = {date.fromisoformat(d.strip()) for d in REACTION_SESSIONS + extra}
        self._state = None                # built from history on the first bar (live start, restart)
        self._prev_target = 0.0
        self._rows, self._fills, self._equity = [], [], []
        if self._mode == 'morning':
            self.schedule.on(self.date_rules.every_day(self._tsla), self.time_rules.before_market_open(self._tsla, 30),
                             self._morning)
        self._intended_qty = None
        if self.live_mode:
            # an MOO that did not fill (no opening cross, halt, broker reject) is replaced by a market order after the open
            self.schedule.on(self.date_rules.every_day(self._tsla), self.time_rules.after_market_open(self._tsla, 15),
                             self._check_unfilled)

    # ------------------------------------------------------------------ state from adjusted history
    def _replay(self, upto_exclusive=None):
        """Fresh F3State replayed over SCALED_RAW daily history. Returns (state, list of (session, a, g, b, p, target))."""
        st = F3State(self._reaction)
        th = list(self.history[TradeBar](self._tsla, self.HISTORY_BARS, Resolution.DAILY, fill_forward=False,
                                         data_normalization_mode=DataNormalizationMode.SCALED_RAW))
        qh = list(self.history[TradeBar](self._qqq, self.HISTORY_BARS + 40, Resolution.DAILY, fill_forward=False,
                                         data_normalization_mode=DataNormalizationMode.SCALED_RAW))
        qmap = {b.time.date(): b.close for b in qh}
        tdates = [b.time.date() for b in th]
        out = []
        # QQQ closes before the first TSLA bar of the window (IPO case: TSLA has no history, QQQ has)
        first = tdates[0] if tdates else date.max
        for b in qh:
            d = b.time.date()
            if d < first and (upto_exclusive is None or d < upto_exclusive):
                st.add_qqq(float(b.close))
        for b in th:
            d = b.time.date()                         # bar START date = the session (independent of end-time setting)
            if upto_exclusive is not None and d >= upto_exclusive:
                break
            if d in qmap:
                st.add_qqq(float(qmap[d]))
            else:
                self.debug(f'WARNING: no QQQ bar for {d}; QQQ window not advanced')
            out.append((d,) + st.step(d, float(b.close)))
        return st, out

    # ------------------------------------------------------------------ MODE 'close': incremental, decide on the bar
    def on_data(self, data: Slice):
        if self._mode == 'morning':
            self._record_equity(data)
            return
        for s in data.splits.values():
            if s.type == SplitType.SPLIT_OCCURRED and self._state is not None:
                (self._state.rescale_tsla if s.symbol == self._tsla else self._state.rescale_qqq)(float(s.split_factor))
                if s.symbol == self._tsla and self._intended_qty is not None:
                    self._intended_qty = int(round(self._intended_qty / float(s.split_factor)))
        for dv in data.dividends.values():
            if self._state is not None and dv.reference_price > 0:
                f = 1.0 - float(dv.distribution) / float(dv.reference_price)
                (self._state.rescale_tsla if dv.symbol == self._tsla else self._state.rescale_qqq)(f)
        tbar = data.bars.get(self._tsla)
        qbar = data.bars.get(self._qqq)
        if self._state is None:
            # first bar after start: rebuild windows + B/P state from history that ENDS BEFORE this bar
            today = (tbar or qbar).time.date() if (tbar or qbar) else self.time.date()
            self._state, past = self._replay(upto_exclusive=today)
            self._prev_target = past[-1][-1] if past else 0.0
        if qbar is not None and not qbar.is_fill_forward:
            self._state.add_qqq(float(qbar.close))
        if tbar is None or tbar.is_fill_forward:
            return
        if qbar is None:
            self.debug(f'WARNING: TSLA bar without QQQ bar on {tbar.time.date()}')
        session = tbar.time.date()
        a, g, b, p, target = self._state.step(session, float(tbar.close))
        self._decide(session, a, g, b, p, target, self._prev_target, float(tbar.close))
        self._prev_target = target
        self._record_equity(data)

    # ------------------------------------------------------------------ MODE 'morning': stateless, before the open
    def _morning(self):
        _, rows = self._replay()
        if not rows:
            return
        session, a, g, b, p, target = rows[-1]
        if session >= self.time.date():
            return                                  # history must end at the previous session
        prev = rows[-2][-1] if len(rows) >= 2 else 0.0
        self._decide(session, a, g, b, p, target, prev, float(self.securities[self._tsla].price))

    # ------------------------------------------------------------------ orders
    def _decide(self, session, a, g, b, p, target, prev_target, price):
        self._rows.append((session.isoformat(), a, g, b, p, target))
        if self.live_mode and (self.time.date() - max(self._reaction)).days > 95:
            self.debug(f'WARNING: last earnings reaction session listed is {max(self._reaction)}; add the next one')
        self._intended_qty = None
        if self.is_warming_up or price <= 0:
            return
        self.transactions.cancel_open_orders(self._tsla)
        h = self.portfolio[self._tsla]
        value = self.portfolio.total_portfolio_value
        current = h.quantity * price / value if value > 0 else 0.0
        if target == prev_target and abs(current - target) <= self._band:
            return
        qty = int(target * value / price) - int(h.quantity)
        if qty != 0:
            self._intended_qty = int(h.quantity) + qty
            self.market_on_open_order(self._tsla, qty, tag=f'{session} target {target:.2f} A{a:.0f}G{g:.0f}B{b:.0f}P{p:.0f}')

    def _check_unfilled(self):
        if self._intended_qty is None:
            return
        for o in self.transactions.get_open_orders(self._tsla):
            self.transactions.cancel_order(o.id)
        diff = self._intended_qty - int(self.portfolio[self._tsla].quantity)
        if diff != 0:
            self.market_order(self._tsla, diff, tag='MOO not filled: market-order fallback')
        self._intended_qty = None

    def on_order_event(self, e: OrderEvent):
        if e.status == OrderStatus.FILLED:
            self._fills.append((self.time.isoformat(), str(e.symbol), float(e.fill_quantity), float(e.fill_price),
                                float(e.order_fee.value.amount)))

    def _record_equity(self, data):
        tbar = data.bars.get(self._tsla)
        if tbar is not None and not tbar.is_fill_forward:
            self._equity.append((tbar.time.date().isoformat(), float(self.portfolio.total_portfolio_value),
                                 float(self.portfolio[self._tsla].quantity), float(tbar.close)))

    def on_end_of_algorithm(self):
        last = max(self._reaction)
        if (self.time.date() - last).days > 100:
            self.debug(f'WARNING: last earnings reaction session in the list is {last}: update REACTION_SESSIONS')
        if not self._out:
            return
        os.makedirs(self._out, exist_ok=True)
        tag = f'{self._mode}_band{self._band:g}' + (f'_slip{self._slip:g}' if self._slip > 0 else '')
        for name, hdr, rows in (('weights', ['date', 'A', 'G', 'B', 'P', 'F3'], self._rows),
                                ('fills', ['time', 'symbol', 'qty', 'price', 'fee'], self._fills),
                                ('equity', ['date', 'tpv', 'shares', 'close'], self._equity)):
            with open(os.path.join(self._out, f'lean_{name}_{tag}.csv'), 'w', newline='') as f:
                w = csv.writer(f)
                w.writerow(hdr)
                w.writerows(rows)
