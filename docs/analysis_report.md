# Nifty 50 Backtesting Results

## Overview

We implemented a backtesting script to analyze the probability of Nifty 50's daily closing zone based on its opening location relative to the previous day's range (PDR).

## Methodology

- **Data**: Nifty 50 1-minute data (2015-2024) resampled to 5-minute candles.
- **Market Hours**: 09:15 to 15:30.
- **PDR Definition**: Range between the highest and lowest *candle body* (Open/Close) of the previous day.
- **Zones**:
  - **Resistance**: PrevDay_Max + 5% of Range Height.
  - **Support**: PrevDay_Min - 5% of Range Height.
  - **Above**: > Resistance
  - **Inside**: Between Support and Resistance
  - **Below**: < Support

## Results

**Total Trading Days Analyzed**: 2601

### Transition Probability Matrix (%)

| Start State | End Above | End Below | End Inside |
| :--- | :--- | :--- | :--- |
| **Above** | **67.35%** | 6.42% | 26.23% |
| **Below** | 4.11% | **71.21%** | 24.68% |
| **Inside** | 22.91% | 24.53% | **52.57%** |

### Key Insights

1. **Trend Continuation**: If the market opens **Above** the resistance, there is a strong probability (67%) it will close Above. Similarly for **Below** (71%).
2. **Range Bound**: If the market opens **Inside** the previous day's range, it is most likely (52%) to stay inside, with an equal chance of breaking out either side (~23-24%).

## Verification

The script `scripts/nifty_backtest.py` was executed and the output was verified against the logic requirements.

- **Data Integrity**: Filtered for valid market hours and handled missing data.

## Strategy Performance (Refined)

We simulated a trading strategy based on the 1st Candle (09:15-09:20) closing zone.

### Rules

- **Entry**: 09:20 (Close of 1st Candle).
- **Direction**:
  - **Long**: If 1st Candle closes **Above** Resistance.
  - **Short**: If 1st Candle closes **Below** Support.
- **Stop Loss (SL)**: 1st Candle Low (Long) / High (Short).
- **Target (TP)**: Entry +/- (2 * Risk). (1:2 Risk:Reward).
- **Exit**: TP hit, SL hit, or End of Day (15:25).

### Results (1 Lot Nifty = 50 Qty)

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 1103 |
| **Win Rate** | 44.97% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |

# Nifty 50 Backtesting Results

## Overview

We implemented a backtesting script to analyze the probability of Nifty 50's daily closing zone based on its opening location relative to the previous day's range (PDR).

## Methodology

- **Data**: Nifty 50 1-minute data (2015-2024) resampled to 5-minute candles.
- **Market Hours**: 09:15 to 15:30.
- **PDR Definition**: Range between the highest and lowest *candle body* (Open/Close) of the previous day.
- **Zones**:
  - **Resistance**: PrevDay_Max + 5% of Range Height.
  - **Support**: PrevDay_Min - 5% of Range Height.
  - **Above**: > Resistance
  - **Inside**: Between Support and Resistance
  - **Below**: < Support

## Results

**Total Trading Days Analyzed**: 2601

### Transition Probability Matrix (%)

| Start State | End Above | End Below | End Inside |
| :--- | :--- | :--- | :--- |
| **Above** | **67.35%** | 6.42% | 26.23% |
| **Below** | 4.11% | **71.21%** | 24.68% |
| **Inside** | 22.91% | 24.53% | **52.57%** |

### Key Insights

1. **Trend Continuation**: If the market opens **Above** the resistance, there is a strong probability (67%) it will close Above. Similarly for **Below** (71%).
2. **Range Bound**: If the market opens **Inside** the previous day's range, it is most likely (52%) to stay inside, with an equal chance of breaking out either side (~23-24%).

## Verification

The script `scripts/nifty_backtest.py` was executed and the output was verified against the logic requirements.

- **Data Integrity**: Filtered for valid market hours and handled missing data.

## Strategy Performance (Refined)

We simulated a trading strategy based on the 1st Candle (09:15-09:20) closing zone.

### Rules

- **Entry**: 09:20 (Close of 1st Candle).
- **Direction**:
  - **Long**: If 1st Candle closes **Above** Resistance.
  - **Short**: If 1st Candle closes **Below** Support.
- **Stop Loss (SL)**: 1st Candle Low (Long) / High (Short).
- **Target (TP)**: Entry +/- (2 * Risk). (1:2 Risk:Reward).
- **Exit**: TP hit, SL hit, or End of Day (15:25).

### Results (1 Lot Nifty = 50 Qty)

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 1103 |
| **Win Rate** | 44.97% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |
| **Above -> Above** | 601 | 44.26% | +2.22 | High frequency, profitable due to R:R. |
| **Below -> Below** | 268 | 42.54% | -2.33 | **Avoid**. Gap down and hold tends to be choppy/reversal prone. |

### Conclusion

- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Gap Down Caution**: A gap down that stays down (`Below -> Below`) actually has a negative expectancy on average. It might be better to wait for a pullback or use a different strategy for these days.

## Inside Day Strategy (Mean Reversion)

We tested a Mean Reversion strategy for days starting **Inside** the range.

- **Logic**: Fade Support/Resistance (Buy Support, Sell Resistance).
- **Target**: Midpoint of Range.
- **Stop**: Just outside the buffer.

### Performance

| Strategy | Count | Win Rate | Avg PnL (Pts) | Total PnL (INR) |
| :--- | :--- | :--- | :--- | :--- |
| **Breakout** | 1103 | 44.97% | +3.29 | +₹1,81,687 |
| **Mean Reversion** | 1215 | **8.81%** | **-1.10** | **-₹66,867** |

### Conclusion

- **Mean Reversion Failed**: The simple "Fade the boundary" strategy had a very low win rate (8.8%). This suggests that when price hits the Support/Resistance on an Inside Day, it often breaks through or doesn't reverse far enough to hit the midpoint.
  - **Support**: PrevDay_Min - 5% of Range Height.
  - **Above**: > Resistance
  - **Inside**: Between Support and Resistance
  - **Below**: < Support

## Results

**Total Trading Days Analyzed**: 2601

### Transition Probability Matrix (%)

| Start State | End Above | End Below | End Inside |
| :--- | :--- | :--- | :--- |
| **Above** | **67.35%** | 6.42% | 26.23% |
| **Below** | 4.11% | **71.21%** | 24.68% |
| **Inside** | 22.91% | 24.53% | **52.57%** |

### Key Insights

1. **Trend Continuation**: If the market opens **Above** the resistance, there is a strong probability (67%) it will close Above. Similarly for **Below** (71%).
2. **Range Bound**: If the market opens **Inside** the previous day's range, it is most likely (52%) to stay inside, with an equal chance of breaking out either side (~23-24%).

## Verification

The script `scripts/nifty_backtest.py` was executed and the output was verified against the logic requirements.

- **Data Integrity**: Filtered for valid market hours and handled missing data.

## Strategy Performance (Refined)

We simulated a trading strategy based on the 1st Candle (09:15-09:20) closing zone.

### Rules

- **Entry**: 09:20 (Close of 1st Candle).
- **Direction**:
  - **Long**: If 1st Candle closes **Above** Resistance.
  - **Short**: If 1st Candle closes **Below** Support.
- **Stop Loss (SL)**: 1st Candle Low (Long) / High (Short).
- **Target (TP)**: Entry +/- (2 * Risk). (1:2 Risk:Reward).
- **Exit**: TP hit, SL hit, or End of Day (15:25).

### Results (1 Lot Nifty = 50 Qty)

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 1103 |
| **Win Rate** | 44.97% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |

# Nifty 50 Backtesting Results

## Overview

We implemented a backtesting script to analyze the probability of Nifty 50's daily closing zone based on its opening location relative to the previous day's range (PDR).

## Methodology

- **Data**: Nifty 50 1-minute data (2015-2024) resampled to 5-minute candles.
- **Market Hours**: 09:15 to 15:30.
- **PDR Definition**: Range between the highest and lowest *candle body* (Open/Close) of the previous day.
- **Zones**:
  - **Resistance**: PrevDay_Max + 5% of Range Height.
  - **Support**: PrevDay_Min - 5% of Range Height.
  - **Above**: > Resistance
  - **Inside**: Between Support and Resistance
  - **Below**: < Support

## Results

**Total Trading Days Analyzed**: 2601

### Transition Probability Matrix (%)

| Start State | End Above | End Below | End Inside |
| :--- | :--- | :--- | :--- |
| **Above** | **67.35%** | 6.42% | 26.23% |
| **Below** | 4.11% | **71.21%** | 24.68% |
| **Inside** | 22.91% | 24.53% | **52.57%** |

### Key Insights

1. **Trend Continuation**: If the market opens **Above** the resistance, there is a strong probability (67%) it will close Above. Similarly for **Below** (71%).
2. **Range Bound**: If the market opens **Inside** the previous day's range, it is most likely (52%) to stay inside, with an equal chance of breaking out either side (~23-24%).

## Verification

The script `scripts/nifty_backtest.py` was executed and the output was verified against the logic requirements.

- **Data Integrity**: Filtered for valid market hours and handled missing data.

## Strategy Performance (Refined)

We simulated a trading strategy based on the 1st Candle (09:15-09:20) closing zone.

### Rules

- **Entry**: 09:20 (Close of 1st Candle).
- **Direction**:
  - **Long**: If 1st Candle closes **Above** Resistance.
  - **Short**: If 1st Candle closes **Below** Support.
- **Stop Loss (SL)**: 1st Candle Low (Long) / High (Short).
- **Target (TP)**: Entry +/- (2 * Risk). (1:2 Risk:Reward).
- **Exit**: TP hit, SL hit, or End of Day (15:25).

### Results (1 Lot Nifty = 50 Qty)

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 1103 |
| **Win Rate** | 44.97% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |
| **Above -> Above** | 601 | 44.26% | +2.22 | High frequency, profitable due to R:R. |
| **Below -> Below** | 268 | 42.54% | -2.33 | **Avoid**. Gap down and hold tends to be choppy/reversal prone. |

### Conclusion

- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Gap Down Caution**: A gap down that stays down (`Below -> Below`) actually has a negative expectancy on average. It might be better to wait for a pullback or use a different strategy for these days.

## Inside Day Strategy (Mean Reversion)

We tested a Mean Reversion strategy for days starting **Inside** the range.

- **Logic**: Fade Support/Resistance (Buy Support, Sell Resistance).
- **Target**: Midpoint of Range.
- **Stop**: Just outside the buffer.

### Performance

| Strategy | Count | Win Rate | Avg PnL (Pts) | Total PnL (INR) |
| :--- | :--- | :--- | :--- | :--- |
| **Breakout** | 1103 | 44.97% | +3.29 | +₹1,81,687 |
| **Mean Reversion** | 1215 | **8.81%** | **-1.10** | **-₹66,867** |

### Conclusion

- **Mean Reversion Failed**: The simple "Fade the boundary" strategy had a very low win rate (8.8%). This suggests that when price hits the Support/Resistance on an Inside Day, it often breaks through or doesn't reverse far enough to hit the midpoint.
- **Recommendation**: Stick to the **Breakout Strategy**, specifically the **Inside -> Below** setup.

## Full Data Verification

- **Total Days Analyzed**: 2601
- **Total Trades Generated**: 2318 (Combined strategies)

## Deep Dive: Above -> Above Setup

We analyzed the **614 days** where the market opened Above and the 1st candle closed Above to optimize the exit target.

### Maximum Favorable Excursion (MFE) Stats

This measures the maximum profit potential (High of the day - Entry) after entering at 09:20.

- **Mean Potential Profit**: 57.68 points
- **Median Potential Profit**: 40.68 points
- **Win Probability (Any Gain)**: 99.19% of trades went positive at some point.

### Target Success Rates

How often a fixed target would be hit:

| Target (Pts) | Success Rate |
| :--- | :--- |
| **20 pts** | **71.34%** |
| **30 pts** | **60.59%** |
| **40 pts** | 50.49% |
| **50 pts** | 42.35% |
| **100 pts** | 16.12% |
We simulated a trading strategy based on the 1st Candle (09:15-09:20) closing zone.

### Rules

- **Entry**: 09:20 (Close of 1st Candle).
- **Direction**:
  - **Long**: If 1st Candle closes **Above** Resistance.
  - **Short**: If 1st Candle closes **Below** Support.
- **Stop Loss (SL)**: 1st Candle Low (Long) / High (Short).
- **Target (TP)**: Entry +/- (2 * Risk). (1:2 Risk:Reward).
- **Exit**: TP hit, SL hit, or End of Day (15:25).

### Results (1 Lot Nifty = 50 Qty)

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 1103 |
| **Win Rate** | 44.97% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |

# Nifty 50 Backtesting Results

## Overview

We implemented a backtesting script to analyze the probability of Nifty 50's daily closing zone based on its opening location relative to the previous day's range (PDR).

## Methodology

- **Data**: Nifty 50 1-minute data (2015-2024) resampled to 5-minute candles.
- **Market Hours**: 09:15 to 15:30.
- **PDR Definition**: Range between the highest and lowest *candle body* (Open/Close) of the previous day.
- **Zones**:
  - **Resistance**: PrevDay_Max + 5% of Range Height.
  - **Support**: PrevDay_Min - 5% of Range Height.
  - **Above**: > Resistance
  - **Inside**: Between Support and Resistance
  - **Below**: < Support

## Results

**Total Trading Days Analyzed**: 2601

### Transition Probability Matrix (%)

| Start State | End Above | End Below | End Inside |
| :--- | :--- | :--- | :--- |
| **Above** | **67.35%** | 6.42% | 26.23% |
| **Below** | 4.11% | **71.21%** | 24.68% |
| **Inside** | 22.91% | 24.53% | **52.57%** |

### Key Insights

1. **Trend Continuation**: If the market opens **Above** the resistance, there is a strong probability (67%) it will close Above. Similarly for **Below** (71%).
2. **Range Bound**: If the market opens **Inside** the previous day's range, it is most likely (52%) to stay inside, with an equal chance of breaking out either side (~23-24%).

## Verification

The script `scripts/nifty_backtest.py` was executed and the output was verified against the logic requirements.

- **Data Integrity**: Filtered for valid market hours and handled missing data.

## Strategy Performance (Refined)

We simulated a trading strategy based on the 1st Candle (09:15-09:20) closing zone.

### Rules

- **Entry**: 09:20 (Close of 1st Candle).
- **Direction**:
  - **Long**: If 1st Candle closes **Above** Resistance.
  - **Short**: If 1st Candle closes **Below** Support.
- **Stop Loss (SL)**: 1st Candle Low (Long) / High (Short).
- **Target (TP)**: Entry +/- (2 * Risk). (1:2 Risk:Reward).
- **Exit**: TP hit, SL hit, or End of Day (15:25).

### Results (1 Lot Nifty = 50 Qty)

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 1103 |
| **Win Rate** | 44.97% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |
| **Above -> Above** | 601 | 44.26% | +2.22 | High frequency, profitable due to R:R. |
| **Below -> Below** | 268 | 42.54% | -2.33 | **Avoid**. Gap down and hold tends to be choppy/reversal prone. |

### Conclusion

- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Gap Down Caution**: A gap down that stays down (`Below -> Below`) actually has a negative expectancy on average. It might be better to wait for a pullback or use a different strategy for these days.

## Inside Day Strategy (Mean Reversion)

We tested a Mean Reversion strategy for days starting **Inside** the range.

- **Logic**: Fade Support/Resistance (Buy Support, Sell Resistance).
- **Target**: Midpoint of Range.
- **Stop**: Just outside the buffer.

### Performance

| Strategy | Count | Win Rate | Avg PnL (Pts) | Total PnL (INR) |
| :--- | :--- | :--- | :--- | :--- |
| **Breakout** | 1103 | 44.97% | +3.29 | +₹1,81,687 |
| **Mean Reversion** | 1215 | **8.81%** | **-1.10** | **-₹66,867** |

### Conclusion

- **Mean Reversion Failed**: The simple "Fade the boundary" strategy had a very low win rate (8.8%). This suggests that when price hits the Support/Resistance on an Inside Day, it often breaks through or doesn't reverse far enough to hit the midpoint.
- **Recommendation**: Stick to the **Breakout Strategy**, specifically the **Inside -> Below** setup.

## Full Data Verification

- **Total Days Analyzed**: 2601
- **Total Trades Generated**: 2318 (Combined strategies)

## Deep Dive: Above -> Above Setup

We analyzed the **614 days** where the market opened Above and the 1st candle closed Above to optimize the exit target.

### Maximum Favorable Excursion (MFE) Stats

This measures the maximum profit potential (High of the day - Entry) after entering at 09:20.

- **Mean Potential Profit**: 57.68 points
- **Median Potential Profit**: 40.68 points
- **Win Probability (Any Gain)**: 99.19% of trades went positive at some point.

### Target Success Rates

How often a fixed target would be hit:

| Target (Pts) | Success Rate |
| :--- | :--- |
| **20 pts** | **71.34%** |
| **30 pts** | **60.59%** |
| **40 pts** | 50.49% |
| **50 pts** | 42.35% |
| **100 pts** | 16.12% |

### Recommendation

- **Conservative**: Target **20-30 points** for a high win rate (60-70%).
- **Balanced**: Target **40 points** (Median MFE is ~40) for a ~50% win rate with better R:R.
- **Aggressive**: Trailing stop is required for targets > 50 points as the probability drops below 40%.

## ATR Stop Loss Analysis

We tested using an ATR-based Stop Loss for the "Above -> Above" setup to see how often it gets hit.

- **Average 14-Day ATR**: ~170 points (This is quite large for an intraday stop).

| Multiplier | Avg SL (Pts) | Hit Rate |
| :--- | :--- | :--- |
| **0.5x ATR** | **85 pts** | **33.11%** |
| **1.0x ATR** | 170 pts | 9.23% |
| **1.5x ATR** | 255 pts | 2.80% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |

# Nifty 50 Backtesting Results

## Overview

We implemented a backtesting script to analyze the probability of Nifty 50's daily closing zone based on its opening location relative to the previous day's range (PDR).

## Methodology

- **Data**: Nifty 50 1-minute data (2015-2024) resampled to 5-minute candles.
- **Market Hours**: 09:15 to 15:30.
- **PDR Definition**: Range between the highest and lowest *candle body* (Open/Close) of the previous day.
- **Zones**:
  - **Resistance**: PrevDay_Max + 5% of Range Height.
  - **Support**: PrevDay_Min - 5% of Range Height.
  - **Above**: > Resistance
  - **Inside**: Between Support and Resistance
  - **Below**: < Support

## Results

**Total Trading Days Analyzed**: 2601

### Transition Probability Matrix (%)

| Start State | End Above | End Below | End Inside |
| :--- | :--- | :--- | :--- |
| **Above** | **67.35%** | 6.42% | 26.23% |
| **Below** | 4.11% | **71.21%** | 24.68% |
| **Inside** | 22.91% | 24.53% | **52.57%** |

### Key Insights

1. **Trend Continuation**: If the market opens **Above** the resistance, there is a strong probability (67%) it will close Above. Similarly for **Below** (71%).
2. **Range Bound**: If the market opens **Inside** the previous day's range, it is most likely (52%) to stay inside, with an equal chance of breaking out either side (~23-24%).

## Verification

The script `scripts/nifty_backtest.py` was executed and the output was verified against the logic requirements.

- **Data Integrity**: Filtered for valid market hours and handled missing data.

## Strategy Performance (Refined)

We simulated a trading strategy based on the 1st Candle (09:15-09:20) closing zone.

### Rules

- **Entry**: 09:20 (Close of 1st Candle).
- **Direction**:
  - **Long**: If 1st Candle closes **Above** Resistance.
  - **Short**: If 1st Candle closes **Below** Support.
- **Stop Loss (SL)**: 1st Candle Low (Long) / High (Short).
- **Target (TP)**: Entry +/- (2 * Risk). (1:2 Risk:Reward).
- **Exit**: TP hit, SL hit, or End of Day (15:25).

### Results (1 Lot Nifty = 50 Qty)

| Metric | Value |
| :--- | :--- |
| **Total Trades** | 1103 |
| **Win Rate** | 44.97% |
| **Total PnL (Points)** | 3,633.75 |
| **Total PnL (INR)** | ₹181,687.50 |
| **Avg Win** | 41.99 pts |
| **Avg Loss** | -28.32 pts |

### Performance by Type

| Type | Count | Win Rate | Total PnL (Pts) |
| :--- | :--- | :--- | :--- |
| **LONG** | 719 | 44.09% | 2,116.95 |
| **SHORT** | 384 | 46.61% | 1,516.80 |

### Conclusion

The strategy is **profitable** over the backtested period. Although the win rate is below 50% (~45%), the positive expectancy comes from the Risk:Reward ratio (Avg Win is significantly larger than Avg Loss).

- **Short trades** have a slightly higher win rate (46.6%) than Long trades (44.1%).
- **Gap Up/Down** days provide viable trading opportunities with this breakout logic.

## Granular Analysis (Open Zone -> Close Zone)

We further refined the analysis to look at the transition of the 1st Candle itself (e.g., Opened Inside PDR -> Closed Above PDR).

### Key Performance by Composite Start State

| Composite Start | Count | Win Rate | Avg PnL (Pts) | Insight |
| :--- | :--- | :--- | :--- | :--- |
| **Inside -> Below** | 115 | **56.52%** | **+18.88** | **Best Performer**. Strong breakdown signal. |
| **Inside -> Above** | 117 | 42.74% | +5.94 | Profitable, but less reliable than breakdown. |
| **Above -> Above** | 601 | 44.26% | +2.22 | High frequency, profitable due to R:R. |
| **Below -> Below** | 268 | 42.54% | -2.33 | **Avoid**. Gap down and hold tends to be choppy/reversal prone. |

### Conclusion

- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Best Setup**: **Inside -> Below**. When the market opens inside the previous day's range and breaks down in the first 5 minutes, it offers the highest probability (56.5%) and best average return.
- **Gap Down Caution**: A gap down that stays down (`Below -> Below`) actually has a negative expectancy on average. It might be better to wait for a pullback or use a different strategy for these days.

## Inside Day Strategy (Mean Reversion)

We tested a Mean Reversion strategy for days starting **Inside** the range.

- **Logic**: Fade Support/Resistance (Buy Support, Sell Resistance).
- **Target**: Midpoint of Range.
- **Stop**: Just outside the buffer.

### Performance

| Strategy | Count | Win Rate | Avg PnL (Pts) | Total PnL (INR) |
| :--- | :--- | :--- | :--- | :--- |
| **Breakout** | 1103 | 44.97% | +3.29 | +₹1,81,687 |
| **Mean Reversion** | 1215 | **8.81%** | **-1.10** | **-₹66,867** |

### Conclusion

- **Mean Reversion Failed**: The simple "Fade the boundary" strategy had a very low win rate (8.8%). This suggests that when price hits the Support/Resistance on an Inside Day, it often breaks through or doesn't reverse far enough to hit the midpoint.
- **Recommendation**: Stick to the **Breakout Strategy**, specifically the **Inside -> Below** setup.

## Full Data Verification

- **Total Days Analyzed**: 2601
- **Total Trades Generated**: 2318 (Combined strategies)

## Deep Dive: Above -> Above Setup

We analyzed the **614 days** where the market opened Above and the 1st candle closed Above to optimize the exit target.

### Maximum Favorable Excursion (MFE) Stats

This measures the maximum profit potential (High of the day - Entry) after entering at 09:20.

- **Mean Potential Profit**: 57.68 points
- **Median Potential Profit**: 40.68 points
- **Win Probability (Any Gain)**: 99.19% of trades went positive at some point.

### Target Success Rates

How often a fixed target would be hit:

| Target (Pts) | Success Rate |
| :--- | :--- |
| **20 pts** | **71.34%** |
| **30 pts** | **60.59%** |
| **40 pts** | 50.49% |
| **50 pts** | 42.35% |
| **100 pts** | 16.12% |

### Recommendation

- **Conservative**: Target **20-30 points** for a high win rate (60-70%).
- **Balanced**: Target **40 points** (Median MFE is ~40) for a ~50% win rate with better R:R.
- **Aggressive**: Trailing stop is required for targets > 50 points as the probability drops below 40%.

## ATR Stop Loss Analysis

We tested using an ATR-based Stop Loss for the "Above -> Above" setup to see how often it gets hit.

- **Average 14-Day ATR**: ~170 points (This is quite large for an intraday stop).

| Multiplier | Avg SL (Pts) | Hit Rate |
| :--- | :--- | :--- |
| **0.5x ATR** | **85 pts** | **33.11%** |
| **1.0x ATR** | 170 pts | 9.23% |
| **1.5x ATR** | 255 pts | 2.80% |

### Insight

- **0.5x ATR (85 pts)** is hit in **1 out of 3 trades**. This is a significant risk if your target is only 30-40 points (Risk:Reward < 1:2).
- **Recommendation**: Since the Median MFE is ~40 points, using a wide ATR stop (85+ points) is **inefficient**.
- **Better Approach**: Use a fixed point stop (e.g., 20-30 pts) or a technical stop (e.g., Low of 1st Candle) rather than ATR, as ATR values are skewed by daily volatility which is often much larger than the intraday breakout move.

## 1:2 Risk:Reward Analysis

We simulated strict **1:2 Risk:Reward** trades for the "Above -> Above" setup to see the Win/Loss distribution.

| Scenario | Win Rate (Target Hit) | Loss Rate (SL Hit) |
| :--- | :--- | :--- |
| **Candle Low SL** (Target = 2x Risk) | 30.12% | **65.39%** |
| **Fixed 20pt SL** (Target = 40 pts) | 33.06% | **63.19%** |
| **Fixed 30pt SL** (Target = 60 pts) | 24.92% | **59.28%** |

### Insight

- **High Failure Rate**: Aiming for a 1:2 R:R results in hitting the Stop Loss **~63-65%** of the time.
- **Conclusion**: This breakout strategy relies on a **high win rate with 1:1 or 1:1.5 R:R** (scalping) rather than catching massive 1:2 or 1:3 moves. The market often gives 20-40 points (high probability) but reverses before hitting larger targets.
