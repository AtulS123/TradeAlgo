"""
Database models for TradeAlgo
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from utils.config import config

Base = declarative_base()

class Ticker(Base):
    """Stock/instrument ticker information"""
    __tablename__ = 'tickers'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200))
    exchange = Column(String(10))  # NSE, BSE
    segment = Column(String(20))  # EQ, FO, etc.
    instrument_type = Column(String(20))  # EQUITY, FUTIDX, OPTIDX, etc.
    lot_size = Column(Integer, default=1)
    tick_size = Column(Float, default=0.05)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    ohlcv_data = relationship("OHLCV", back_populates="ticker", cascade="all, delete-orphan")


class OHLCV(Base):
    """OHLCV (candlestick) data"""
    __tablename__ = 'ohlcv'
    
    id = Column(Integer, primary_key=True)
    ticker_id = Column(Integer, ForeignKey('tickers.id'), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    timeframe = Column(String(20), nullable=False, index=True)  # 1minute, 5minute, day, etc.
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    
    # Relationships
    ticker = relationship("Ticker", back_populates="ohlcv_data")
    
    # Composite unique constraint
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class StrategyModel(Base):
    """Strategy configuration and metadata"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    code = Column(Text)  # Strategy code
    parameters = Column(Text)  # JSON string of parameters
    
    # Configuration
    symbols = Column(Text)  # JSON array of symbols
    timeframe = Column(String(20))
    capital = Column(Float)
    position_size = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")


class Backtest(Base):
    """Backtest results"""
    __tablename__ = 'backtests'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)
    
    # Configuration
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    
    # Results
    final_capital = Column(Float)
    total_return_percent = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    
    # Risk metrics
    max_drawdown = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    
    # Additional metrics (JSON)
    metrics = Column(Text)  # JSON string of all metrics
    
    # Status
    status = Column(String(20))  # RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)
    
    # Relationships
    strategy = relationship("StrategyModel", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")


class Trade(Base):
    """Individual trade records"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    backtest_id = Column(Integer, ForeignKey('backtests.id'), index=True)
    
    # Trade details
    symbol = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    
    # Timestamps
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    
    # P&L
    pnl = Column(Float)
    pnl_percent = Column(Float)
    
    # Costs
    brokerage = Column(Float)
    taxes = Column(Float)
    
    # Status
    status = Column(String(20))  # OPEN, CLOSED
    
    # Relationships
    backtest = relationship("Backtest", back_populates="trades")


class Alert(Base):
    """System alerts and notifications"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    level = Column(String(20), nullable=False)  # INFO, WARNING, CRITICAL
    category = Column(String(50))  # SYSTEM, TRADE, DATA, etc.
    message = Column(Text, nullable=False)
    details = Column(Text)  # JSON string
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)


# Database initialization
def init_db():
    """Initialize database and create tables"""
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Get database session"""
    engine = create_engine(config.database_url)
    Session = sessionmaker(bind=engine)
    return Session()
