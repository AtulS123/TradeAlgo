# TradeAlgo 🚀

**Automated Algorithmic Trading Platform for Indian Stock Markets**

A comprehensive trading system for NSE/BSE markets supporting strategy development, backtesting, paper trading, and live execution via Kite Connect API.

## Features

### 🎯 Core Capabilities
- **Strategy Development**: Code-based strategy creation with 50+ technical indicators
- **Backtesting Engine**: Realistic backtesting with slippage, brokerage, and taxes
- **Paper Trading**: Risk-free testing with real-time market simulation
- **Live Trading**: Automated execution via Kite Connect API
- **System Monitoring**: Health diagnostics and accuracy scoring
- **Strategy Rating**: 0-100 scoring system to rank strategies

### 📊 Indian Market Focus
- Nifty 50, Bank Nifty, Sensex stocks
- F&O instruments (Nifty, Bank Nifty futures/options)
- NSE/BSE trading calendar with holidays
- Pre-configured watchlists

### 📈 Technical Indicators (50+)
- **Trend**: SMA, EMA, MACD, Supertrend, Ichimoku, etc.
- **Momentum**: RSI, Stochastic, CCI, MFI, etc.
- **Volatility**: Bollinger Bands, ATR, Keltner Channels, etc.
- **Volume**: VWAP, OBV, Volume Profile, etc.
- **Custom**: Import from TradingView, TA-Lib integration

### 🛡️ Risk Management
- Position sizing controls
- Stop-loss and take-profit automation
- Daily loss limits
- Emergency stop mechanisms
- Real-time P&L tracking

## Quick Start

### Prerequisites
- Python 3.10+
- Kite Connect API subscription
- Windows/Linux/Mac

### Installation

1. **Clone the repository**
```bash
cd c:\Users\atuls\Startup
cd TradeAlgo
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure credentials**
```bash
# Copy .env.example to .env and add your Kite API credentials
copy .env.example .env
# Edit .env with your API key and secret
```

5. **Run the application**
```bash
# Start the backend API
python -m backend.main

# In another terminal, start the frontend
cd frontend
npm install
npm start
```

## Project Structure

```
TradeAlgo/
├── core/              # Trading engine (strategy, backtest, paper, live)
├── data/              # Data fetching and storage
├── strategies/        # Trading strategies
├── indicators/        # Technical indicators library
├── brokers/           # Broker integrations (Kite)
├── utils/             # Utilities (config, logger, metrics)
├── monitoring/        # System health and diagnostics
├── rating/            # Strategy rating system
├── market_data/       # Indian market data
├── backend/           # FastAPI backend
├── frontend/          # React dashboard
└── config/            # Configuration files
```

## Usage

### 1. Create a Strategy

```python
from core.strategy import Strategy
from indicators.trend import SMA

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(
            name="My SMA Strategy",
            symbols=["RELIANCE", "TCS"],
            capital=100000
        )
        
    def on_data(self, symbol, bar):
        # Calculate indicators
        sma_fast = SMA(self.data[symbol]['close'], period=10)
        sma_slow = SMA(self.data[symbol]['close'], period=20)
        
        # Generate signals
        if sma_fast[-1] > sma_slow[-1]:
            self.buy(symbol)
        elif sma_fast[-1] < sma_slow[-1]:
            self.sell(symbol)
```

### 2. Backtest the Strategy

```python
from core.backtest import Backtest

backtest = Backtest(
    strategy=MyStrategy(),
    start_date="2023-01-01",
    end_date="2024-01-01"
)

results = backtest.run()
print(results.get_metrics())
```

### 3. Paper Trade

```python
from core.paper_trading import PaperTrading

paper = PaperTrading(strategy=MyStrategy())
paper.start()
```

### 4. Go Live (with caution!)

```python
from core.live_trading import LiveTrading

live = LiveTrading(
    strategy=MyStrategy(),
    dry_run=False  # Set to True for testing
)
live.start()
```

## Configuration

Edit `config/config.yaml` to customize:
- Trading hours
- Risk parameters
- Slippage and brokerage
- Alert settings
- And more...

## Safety Features

⚠️ **Important**: Always test strategies thoroughly before live trading!

- Start with paper trading for at least 1-2 weeks
- Use minimal capital initially
- Set strict stop-losses
- Monitor system health dashboard
- Review strategy ratings

## Development Status

- [x] Phase 1: Project Foundation
- [ ] Phase 2: Data Management & Indicators
- [ ] Phase 3: Backtesting Engine
- [ ] Phase 4: Paper Trading
- [ ] Phase 5: Live Trading
- [ ] Phase 6: Indian Market Data
- [ ] Phase 7: System Monitoring
- [ ] Phase 8: Strategy Rating
- [ ] Phase 9: Web Dashboard

## Contributing

This is a personal project. Feel free to fork and customize for your needs.

## Disclaimer

**This software is for educational purposes only. Trading in financial markets involves substantial risk. Past performance does not guarantee future results. Use at your own risk.**

## License

MIT License

## Support

For issues or questions, please check the documentation or create an issue.

---

**Happy Trading! 📈**
