# Trading Strategies Documentation

This document outlines the rules and logic for the implemented trading strategies.

## Entry Strategies

### 1. VWAP "Check-Back" (Trend Continuation)

**File:** `strategies/entry/vwap_trend.py`
**Type:** Trend Following / Pullback
**Best For:** Strong trend days

**Logic:** Institutions often defend the Volume Weighted Average Price (VWAP). When a trending stock pulls back to this line, algos reload positions.

**Rules:**

- **Trend Filter:** Price must be above VWAP for > 15 minutes (3 bars on 5-min chart).
- **Trigger:** Price touches the VWAP line but does not close below it. Enter Long when the next candle closes higher than the "touch" candle's high.

### 2. Multi-Timeframe EMA Alignment (The "Royal Flush")

**File:** `strategies/entry/ema_alignment.py`
**Type:** Trend Following
**Best For:** Catching the biggest move of the day

**Logic:** You only trade when the short-term momentum aligns with the long-term trend.

**Rules:**

- **Filter (1-Hour Chart):** Price must be above the 20 EMA.
- **Trigger (5-Minute Chart):** Enter Long when the 9 EMA crosses above the 21 EMA.
- **Constraint:** If the 1-Hour is bearish, ignore all 5-minute buy signals.

### 3. 15-Minute Opening Range Breakout (ORB)

**File:** `strategies/entry/orb.py`
**Type:** Breakout
**Best For:** Volatile stocks at the market open

**Logic:** The first 15 minutes clear out overnight orders. A break of this range often sets the trend for the next 2 hours.

**Rules:**

- **Setup:** Mark the High and Low of the first 15 minutes (9:30–9:45 AM).
- **Trigger:** Enter if a 5-minute candle closes outside this range with volume > 110% of average.

### 4. Supply/Demand Structure Shift (The "Smart Money" Entry)

**File:** `strategies/entry/structure_shift.py`
**Type:** Reversal
**Best For:** Reversal trading (catching the bottom)

**Logic:** It waits for a key Swing High to be broken, indicating that sellers are exhausted and buyers have taken control.

**Rules:**

- **Setup:** Identify a downtrend with Lower Highs and Lower Lows.
- **Trigger:** Enter Long immediately after a candle closes above the most recent Lower High (breaking the structure).
- **Filter:** The breakout candle must be a "marubozu" (full body, small wicks) indicating conviction.

### 5. RSI + Bollinger Band Extremes (Mean Reversion)

**File:** `strategies/entry/mean_reversion.py`
**Type:** Mean Reversion
**Best For:** Choppy/Sideways markets (lunch hour)

**Logic:** Prices rarely stay 2 standard deviations away from the mean for long.

**Rules:**

- **Setup:** Bollinger Bands (Length 20, StdDev 2.5) and RSI (Length 14).
- **Trigger (Short):** Price touches the Upper Band AND RSI > 75.
- **Trigger (Long):** Price touches the Lower Band AND RSI < 25.

---

## Exit Strategies

### 1. ATR Trailing Stop (The "Chandelier")

**File:** `strategies/exit/trailing_stop.py`
**Type:** Trend Following

**Logic:** Keeps you in the trade as long as volatility is normal. Exits only when the trend structure breaks.
**Rule:** Set a trailing stop at Highest Price - (3.0 * ATR).

### 2. The "N-Bar" Time Stop (The Stale Exit)

**File:** `strategies/exit/time_stop.py`
**Type:** Efficiency

**Logic:** If a trade doesn't work immediately, it's likely a dud.
**Rule:** If the trade is not profitable after 6 bars (30 minutes on a 5-min chart), close it immediately.

### 3. Technical Target (Fixed Reward-to-Risk)

**File:** `strategies/exit/profit_target.py`
**Type:** Profit Taking

**Logic:** Guarantees a mathematical edge.
**Rule:** Place a Limit Sell order at Entry Price + (2.5 * Risk).

### 4. Indicator Reversal (The "Signal Flip")

**File:** `strategies/exit/indicator_exit.py`
**Type:** Adaptive

**Logic:** If the market condition changes, your reason for holding the trade is invalid.
**Rule:**

- **Trend Trades:** Exit if the 9 EMA crosses back below the 21 EMA.
- **Reversion Trades:** Exit if price returns to the VWAP line.

### 5. Break-Even "Free Ride"

**File:** `strategies/exit/breakeven.py`
**Type:** Capital Protection

**Logic:** Eliminates risk once the trade moves in your favor.
**Rule:** Once profit reaches 1R, move your Hard Stop Loss to your Entry Price.
