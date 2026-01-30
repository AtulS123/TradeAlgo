# Live Trading Architecture Plan

This document outlines the technical architecture for moving the TradeAlgo system from backtesting to a robust, event-driven live trading environment.

## Core Architecture: Producer-Consumer Model

To ensure high reliability and low latency, the system adopts a **Producer-Consumer Architecture**. This decouples data ingestion from strategy processing, preventing heavy calculations from blocking critical market data updates.

### High-Level Diagram

The system consists of four independent modules:

1. **The Sentinel** (Authentication & Session)
2. **The Producer** (Data Ingestion)
3. **The Consumer** (Strategy Engine)
4. **The Gatekeeper** (Risk & Execution)

---

## Component Breakdown

### 1. The Sentinel (Session Management)

**Role:** Automates authentication and token management.

- **Trigger:** On candle close (timestamp change), it triggers the strategy logic.
- **Signal Generation:** Runs indicator modules on the closed candle. If a signal is found, creates an "Order Object" payload and sends it to the Gatekeeper.
- **Parity:** Uses the exact same Strategy classes as the backtesting engine to ensure logic consistency.

### 4. The Gatekeeper (Execution & Risk)

**Role:** Validates orders and manages risk before execution.

- **Rate Limiting:** Implements a "Token Bucket" algorithm to enforce API rate limits (e.g., max 5 orders/sec).
- **Kill Switch:** Checks live MTM (Mark-to-Market) before every order. If loss > 2% of capital, rejects order and halts system.
- **Slippage Protection:** Converts "Market Orders" to "Limit Orders" with a marketable buffer (e.g., LTP + 0.5%) to avoid freak trade execution.

---

## Infrastructure & Stack

| Component | Recommendation | Reason |
| :--- | :--- | :--- |
| **Server** | **AWS EC2 (Mumbai / ap-south-1)** | Low latency (~2-10ms) to NSE exchange. |
| **Database** | **Redis (In-Memory)** | Ultra-low latency message broker between Producer and Consumer. |
| **Language** | **Python 3.10+** | Native `asyncio` support and rich financial ecosystem. |
| **Process Manager** | **Docker / Supervisor** | Auto-restart capabilities for crash resilience. |

---

## Recommended Project Structure

```text
/AlgoTradingSetup
│
├── /core
│   ├── authentication.py    # The Sentinel: Login & Token refresh
│   ├── kite_wrapper.py      # Wrapper for API calls with rate limiting
│   └── risk_manager.py      # The Gatekeeper: Kill switch & Validation
│
├── /data
│   ├── ticker_stream.py     # The Producer: Async WebSocket
│   └── candle_builder.py    # Utility to convert Ticks -> Candles
│
├── /engine
│   ├── consumer.py          # The Consumer: Main Strategy Loop
│   └── order_manager.py     # Order lifecycle management
│
├── /strategies
│   ├── momentum_scanner.py  # Entry Logic (Equity)
│   └── straddle_manager.py  # Execution Logic (Options)
│
├── /logs                    # Structured logs (JSON format preferred)
├── .env                     # Secrets (API Keys, Redis URL)
└── main.py                  # Entry point (Supervisor)
```

---

## Refinements & Best Practices

1. **Hybrid Strategy Approach:**
    - Use **Equity Momentum** to identify trend direction.
    - Execute using **Options Selling** (e.g., Sell PE on Bullish Equity trend) to benefit from Theta decay and improve consistency.

2. **Monitoring & Alerting:**
    - Implement **Heartbeat Monitoring**: If the Producer stops pushing ticks for > 5 seconds, alert via Telegram/Slack.
    - **Latency Tracking**: Measure time from `Tick Received` -> `Order Sent` to optimize performance.

3. **Error Handling:**
    - **Exponential Backoff**: For network reconnections in the Sentinel and Producer.
    - **Circuit Breakers**: Pause trading if error rate exceeds threshold (e.g., 5 failed orders in 1 minute).

4. **Data Persistence:**
    - While Redis is for real-time, asynchronously dump candles to a **TimescaleDB** or **SQLite** for post-trade analysis and debugging.
