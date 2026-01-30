
## Proposed Changes

### New Script

#### [NEW] [nifty_backtest.py](file:///C:/Users/atuls/Startup/TradeAlgo/scripts/nifty_backtest.py)

- **Libraries**: `pandas`, `numpy`.
- **Steps**:
    1. **Load Data**: Read CSV, parse dates.
    2. **Resample**: Convert 1-min to 5-min candles (Open=first, High=max, Low=min, Close=last, Volume=sum).
    3. **Filter**: Keep only 09:15 - 15:30.

## Proposed Changes

### New Script

#### [NEW] [nifty_backtest.py](file:///C:/Users/atuls/Startup/TradeAlgo/scripts/nifty_backtest.py)

- **Libraries**: `pandas`, `numpy`.
- **Steps**:
    1. **Load Data**: Read CSV, parse dates.
    2. **Resample**: Convert 1-min to 5-min candles (Open=first, High=max, Low=min, Close=last, Volume=sum).
    3. **Filter**: Keep only 09:15 - 15:30.

## Verification Plan

### Automated Tests

- Run the script: `python scripts/nifty_backtest.py`
- Check output for:
  - Recommendation for optimal target.
  - Total trading days count.
  - No errors.

## ATR Stop Loss Analysis (Phase 6)

### Goal

Determine the effectiveness of an ATR-based Stop Loss for the "Above -> Above" setup.

### Logic

1. **ATR Calculation**:
    - Calculate Daily High, Low, Close from 5-min data.
    - Calculate True Range (TR) = Max(High-Low, |High-PrevClose|, |Low-PrevClose|).
    - Calculate 14-day Simple Moving Average (SMA) of TR to get ATR.
2. **Simulation**:
    - Filter for "Above -> Above" days.
    - Entry: 09:20 Close.
    - Stop Loss Levels: Entry - (Multiplier * ATR) for Multipliers [0.5, 1.0, 1.5, 2.0].
    - Check if SL is hit during the day (Low <= SL).
3. **Metrics**:
    - **Average ATR**: What is the typical point value for 1 ATR?
    - **SL Hit Rate**: % of trades where SL is hit for each multiplier.
4. **Output**:
    - Table showing Multiplier, Avg SL Points, and Hit Rate.
