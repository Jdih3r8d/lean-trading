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
### Two independent long-only TSLA modules, each sized at 50% of the portfolio:
###   A (trend):        long while SMA(10) > SMA(30) of the daily close; exit when SMA(10) < SMA(30).
###   B (capitulation): buy when the close is >= 12% below the close 5 sessions earlier;
###                     sell at the open 3 sessions after entry.
### Signals are computed on the daily close and executed with market-on-open orders the next session.
### Research and statistics: Research/TeslaStrategy/README.md
### </summary>
### <meta name="tag" content="using data" />
### <meta name="tag" content="indicators" />
### <meta name="tag" content="trading and orders" />
class TeslaTrendCapitulationAlgorithm(QCAlgorithm):

    MODULE_WEIGHT = 0.5
    FAST, SLOW = 10, 30
    DROP_LOOKBACK, DROP_THRESHOLD, DROP_HOLD = 5, 0.12, 3

    def initialize(self):
        self.set_start_date(2011, 1, 1)
        self.set_cash(100000)
        self._tsla = self.add_equity("TSLA", Resolution.DAILY).symbol
        self._fast = self.sma(self._tsla, self.FAST, Resolution.DAILY)
        self._slow = self.sma(self._tsla, self.SLOW, Resolution.DAILY)
        self._closes = RollingWindow[float](self.DROP_LOOKBACK + 1)
        self.set_warm_up(self.SLOW + 5, Resolution.DAILY)

        self._qty_a = 0
        self._qty_b = 0
        self._bars_since_b_signal = None

    def on_data(self, data: Slice):
        bar = data.bars.get(self._tsla)
        if bar is None:
            return
        self._closes.add(bar.close)
        if self.is_warming_up or not (self._slow.is_ready and self._closes.is_ready):
            return

        # Module A: trend following on the SMA(10)/SMA(30) relationship.
        fast, slow = self._fast.current.value, self._slow.current.value
        if self._qty_a == 0 and fast > slow:
            self._qty_a = self._size(bar.close)
            if self._qty_a > 0:
                self.market_on_open_order(self._tsla, self._qty_a, tag="A entry: SMA10 > SMA30")
        elif self._qty_a > 0 and fast < slow:
            self.market_on_open_order(self._tsla, -self._qty_a, tag="A exit: SMA10 < SMA30")
            self._qty_a = 0

        # Module B: buy a 5-session drop of 12% or more, hold 3 sessions.
        if self._qty_b > 0:
            self._bars_since_b_signal += 1
            if self._bars_since_b_signal >= self.DROP_HOLD:
                self.market_on_open_order(self._tsla, -self._qty_b, tag="B exit: time stop")
                self._qty_b = 0
                self._bars_since_b_signal = None
            return

        drop = bar.close / self._closes[self.DROP_LOOKBACK] - 1
        if drop <= -self.DROP_THRESHOLD:
            self._qty_b = self._size(bar.close)
            if self._qty_b > 0:
                self.market_on_open_order(self._tsla, self._qty_b, tag=f"B entry: 5-day drop {drop:.1%}")
                self._bars_since_b_signal = 0

    def _size(self, price: float) -> int:
        return int(self.MODULE_WEIGHT * self.portfolio.total_portfolio_value / price)
