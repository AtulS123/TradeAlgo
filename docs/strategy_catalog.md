# Strategy Catalog

This document lists all available trading strategies in the codebase, categorized by their function: Entry, Exit (Risk Management), and Market Regime.

## 1. Entry Strategies

These strategies define the conditions for opening a new position.

| ID | Strategy Name | Type | Description | Source File |
| :--- | :--- | :--- | :--- | :--- |
| **EN-01** | **VWAP Trend Continuation** | Trend | Enters when price is above VWAP and 20 EMA, often on a pullback. | `research_lab/vectorized_logic.py` |
| **EN-02** | **EMA Alignment ("Royal Flush")** | Trend | Enters when Fast EMA > Slow EMA and Price > Trend EMA (200 EMA). | `research_lab/vectorized_logic.py` |
| **EN-03** | **Opening Range Breakout (ORB)** | Breakout | Enters when price breaks the High (Long) or Low (Short) of the first 15 minutes. | `research_lab/vectorized_logic.py` |
| **EN-04** | **Structure Shift** | Reversal | Enters when price breaks a recent Swing High (Long) or Swing Low (Short). | `research_lab/vectorized_logic.py` |
| **EN-05** | **RSI + Bollinger Mean Reversion** | Mean Rev | Enters Long when RSI < 30 & Price < Lower BB. Short when RSI > 70 & Price > Upper BB. | `research_lab/vectorized_logic.py` |
| **EN-06** | **Daily Zone Breakout** | Breakout | Enters at 09:20 if the first 5-min candle closes Above Resistance or Below Support. | `scripts/nifty_backtest.py` |
| **EN-07** | **Inside Day Fade** | Mean Rev | On Inside Days, Sells at Resistance and Buys at Support targeting the range midpoint. | `scripts/nifty_backtest.py` |

## 2. Exit & Risk Management Strategies

These strategies define when to close a position, either for profit or loss.

| ID | Strategy Name | Type | Description | Source File |
| :--- | :--- | :--- | :--- | :--- |
| **EX-01** | **ATR Trailing Stop** | Trailing SL | Trailing stop set at `Highest Price - (Multiplier * ATR)`. | `strategies/exit/trailing_stop.py` |
| **EX-02** | **Time-Based Stop ("N-Bar")** | Time Stop | Closes the trade if not profitable after N bars (e.g., 30 mins). | `strategies/exit/time_stop.py` |
| **EX-03** | **Fixed Risk:Reward Target** | Profit Target | Exits at a fixed multiple of risk (e.g., Entry + 2 * Risk). | `strategies/exit/profit_target.py` |
| **EX-04** | **Indicator Reversal** | Signal Exit | Exits when the entry condition invalidates (e.g., EMA crossover back). | `strategies/exit/indicator_exit.py` |
| **EX-05** | **Break-Even Stop** | Protection | Moves SL to Entry Price once the trade reaches 1R profit. | `strategies/exit/breakeven.py` |
| **EX-06** | **Candle High/Low Stop** | Technical SL | Places initial SL at the Low (Long) or High (Short) of the signal candle. | `scripts/nifty_backtest.py` |

## 3. Market Regime Strategies

These strategies classify the market environment to determine which Entry/Exit strategies to deploy.

| ID | Strategy Name | Type | Description | Source File |
| :--- | :--- | :--- | :--- | :--- |
| **RG-01** | **Gaussian HMM Regime** | ML / Probabilistic | Uses Hidden Markov Models to classify market into **Bull Quiet, Bull Volatile, Bear Quiet, Bear Volatile, Sideways** based on Log Returns and Volatility. | `research_lab/market_regime.py` |
| **RG-02** | **Daily Zone Classification** | Rule-Based | Classifies day as **Above, Inside, or Below** based on Previous Day's Range (PDR) and a 5% buffer. | `scripts/nifty_backtest.py` |
