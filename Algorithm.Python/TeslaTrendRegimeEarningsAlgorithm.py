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

from AlgorithmImports import *

### <summary>
### Long-only TSLA strategy with three sleeves, evaluated on daily closes and traded at the next open:
###   A (trend, gated by the market): SMA10 > SMA30 of TSLA AND SMA10 > SMA30 of QQQ.
###   B (capitulation): close at least 12% below the close 5 sessions earlier; hold 3 sessions.
###   P (post-earnings continuation): on an earnings reaction session, close at least 3% above the last
###      pre-release close; hold 10 sessions.
### Target weight = min(1, 0.5*A + 0.5*B + 0.5*P). Research: Research/TeslaStrategy/README.md
### </summary>
### <meta name="tag" content="using data" />
### <meta name="tag" content="indicators" />
### <meta name="tag" content="trading and orders" />
class TeslaTrendRegimeEarningsAlgorithm(QCAlgorithm):

    SLEEVE = 0.5
    FAST, SLOW = 10, 30
    DROP_LOOKBACK, DROP_THRESHOLD, DROP_HOLD = 5, 0.12, 3
    EARNINGS_REACTION, EARNINGS_HOLD = 0.03, 10
    REBALANCE_BAND = 0.10

    # First session whose open reflects each quarterly results release (65 after the close, 1 before the open).
    # Must be extended every quarter for live trading (Tesla announces the date 2-3 weeks ahead).
    EARNINGS_REACTION_SESSIONS = [
        '20100805', '20101110', '20110216', '20110505', '20110804', '20111103', '20120216', '20120510',
        '20120726', '20121105', '20130221', '20130509', '20130808', '20131106', '20140220', '20140508',
        '20140801', '20141106', '20150212', '20150507', '20150806', '20151104', '20160211', '20160505',
        '20160804', '20161027', '20170223', '20170504', '20170803', '20171102', '20180208', '20180503',
        '20180802', '20181025', '20190131', '20190425', '20190725', '20191024', '20200130', '20200430',
        '20200723', '20201022', '20210128', '20210427', '20210727', '20211021', '20220127', '20220421',
        '20220721', '20221020', '20230126', '20230420', '20230720', '20231019', '20240125', '20240424',
        '20240724', '20241024', '20250130', '20250423', '20250724', '20251023', '20260129', '20260423',
        '20260723', '20261022',
    ]

    def initialize(self):
        self.set_start_date(2010, 7, 1)
        self.set_cash(100000)
        self._tsla = self.add_equity("TSLA", Resolution.DAILY).symbol
        self._qqq = self.add_equity("QQQ", Resolution.DAILY).symbol
        self._fast = self.sma(self._tsla, self.FAST, Resolution.DAILY)
        self._slow = self.sma(self._tsla, self.SLOW, Resolution.DAILY)
        self._qqq_fast = self.sma(self._qqq, self.FAST, Resolution.DAILY)
        self._qqq_slow = self.sma(self._qqq, self.SLOW, Resolution.DAILY)
        self.set_warm_up(self.SLOW + 5, Resolution.DAILY)
        self.set_benchmark(self._tsla)

        self._earnings = {datetime.strptime(d, '%Y%m%d').date() for d in self.EARNINGS_REACTION_SESSIONS}
        self._closes = RollingWindow[float](self.DROP_LOOKBACK + 1)
        self._bar = 0                 # TSLA sessions seen
        self._b_until = self._b_next = 0
        self._p_until = self._p_next = 0
        self._target = 0.0

    def on_data(self, data: Slice):
        bar = data.bars.get(self._tsla)
        if bar is None:
            return
        self._closes.add(bar.close)
        n = self._bar
        self._bar += 1
        if not self._closes.is_ready:
            return

        # B: capitulation, weight 1 on this close and the next 2 (buy next open, sell at the open 3 sessions later).
        # Signals while holding and on the exit-decision close are ignored.
        if n >= self._b_next and bar.close / self._closes[self.DROP_LOOKBACK] - 1 <= -self.DROP_THRESHOLD:
            self._b_until, self._b_next = n + self.DROP_HOLD, n + self.DROP_HOLD + 1
        b = 1.0 if n < self._b_until else 0.0

        # P: post-earnings continuation after a reaction of at least +3% versus the last pre-release close.
        if (n >= self._p_next and bar.time.date() in self._earnings
                and bar.close / self._closes[1] - 1 >= self.EARNINGS_REACTION):
            self._p_until, self._p_next = n + self.EARNINGS_HOLD, n + self.EARNINGS_HOLD + 1
        p = 1.0 if n < self._p_until else 0.0

        if self.is_warming_up or not (self._slow.is_ready and self._qqq_slow.is_ready):
            return

        # A: TSLA trend, only while the Nasdaq-100 trend agrees.
        a = 1.0 if (self._fast.current.value > self._slow.current.value
                    and self._qqq_fast.current.value > self._qqq_slow.current.value) else 0.0

        target = min(1.0, self.SLEEVE * (a + b + p))
        self._rebalance(target, bar.close, f"A={a:.0f} B={b:.0f} P={p:.0f}")

    def _rebalance(self, target: float, price: float, tag: str):
        holding = self.portfolio[self._tsla]
        value = self.portfolio.total_portfolio_value
        current = holding.quantity * price / value if value > 0 else 0.0
        changed = target != self._target
        self._target = target
        if not changed and abs(current - target) <= self.REBALANCE_BAND:
            return
        quantity = int(target * value / price) - holding.quantity
        if quantity != 0:
            self.market_on_open_order(self._tsla, quantity, tag=f"target {target:.2f} ({tag})")
