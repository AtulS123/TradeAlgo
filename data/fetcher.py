"""
Data fetcher for Kite Connect API
"""

import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from kiteconnect import KiteConnect

# from utils.config import config  # Removed to avoid config dependency
from utils.logger import logger
from data.storage import get_session, Ticker, OHLCV


class RateLimiter:
    """Rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 3, time_window: float = 1.0):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum calls allowed in time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Remove old calls outside time window
        self.calls = [t for t in self.calls if now - t < self.time_window]
        
        # Wait if at limit
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
                self.calls = []
        
        # Record this call
        self.calls.append(time.time())


class KiteDataFetcher:
    """
    Fetch historical and real-time data from Kite Connect API
    """
    
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        """
        Initialize Kite data fetcher
        
        Args:
            api_key: Kite API key (from config if not provided)
            access_token: Kite access token
        """
        self.api_key = api_key or config.kite_api_key
        self.access_token = access_token
        
        if not self.api_key:
            raise ValueError("Kite API key not configured")
        
        self.kite = KiteConnect(api_key=self.api_key)
        
        if self.access_token:
            self.kite.set_access_token(self.access_token)
        
        # Rate limiter (3 requests per second)
        self.rate_limiter = RateLimiter(max_calls=3, time_window=1.0)
        
        logger.info("KiteDataFetcher initialized")
    
    def get_login_url(self) -> str:
        """
        Get Kite login URL for authentication
        
        Returns:
            Login URL
        """
        return self.kite.login_url()
    
    def set_access_token_from_request_token(self, request_token: str, api_secret: Optional[str] = None) -> str:
        """
        Generate access token from request token
        
        Args:
            request_token: Request token from Kite redirect
            api_secret: API secret (from config if not provided)
            
        Returns:
            Access token
        """
        api_secret = api_secret or config.kite_api_secret
        
        if not api_secret:
            raise ValueError("Kite API secret not configured")
        
        data = self.kite.generate_session(request_token, api_secret=api_secret)
        self.access_token = data["access_token"]
        self.kite.set_access_token(self.access_token)
        
        logger.info("Access token generated successfully")
        return self.access_token
    
    def get_instruments(self, exchange: str = "NSE") -> pd.DataFrame:
        """
        Get list of all instruments
        
        Args:
            exchange: Exchange (NSE, BSE, NFO, etc.)
            
        Returns:
            DataFrame of instruments
        """
        self.rate_limiter.wait_if_needed()
        
        instruments = self.kite.instruments(exchange)
        df = pd.DataFrame(instruments)
        
        logger.info(f"Fetched {len(df)} instruments from {exchange}")
        return df
    
    def get_historical_data(
        self,
        symbol: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "day",
        exchange: str = "NSE"
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data
        
        Args:
            symbol: Trading symbol (e.g., "RELIANCE")
            from_date: Start date
            to_date: End date
            interval: Timeframe (minute, 5minute, 15minute, day, etc.)
            exchange: Exchange
            
        Returns:
            DataFrame with OHLCV data
        """
        self.rate_limiter.wait_if_needed()
        
        # Get instrument token
        instrument_token = self._get_instrument_token(symbol, exchange)
        
        if not instrument_token:
            raise ValueError(f"Instrument token not found for {symbol}")
        
        # Fetch data
        try:
            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
            
            df = pd.DataFrame(data)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.rename(columns={'date': 'timestamp'})
                df['symbol'] = symbol
                df['timeframe'] = interval
            
            logger.info(f"Fetched {len(df)} bars for {symbol} ({interval})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise
    
    def _get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """
        Get instrument token for a symbol
        
        Args:
            symbol: Trading symbol
            exchange: Exchange
            
        Returns:
            Instrument token
        """
        instruments = self.get_instruments(exchange)
        
        # Try exact match first
        match = instruments[instruments['tradingsymbol'] == symbol]
        
        if match.empty:
            # Try with -EQ suffix for NSE
            match = instruments[instruments['tradingsymbol'] == f"{symbol}-EQ"]
        
        if not match.empty:
            return int(match.iloc[0]['instrument_token'])
        
        logger.warning(f"Instrument token not found for {symbol}")
        return None
    
    def save_to_database(self, df: pd.DataFrame, symbol: str):
        """
        Save OHLCV data to database
        
        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol
        """
        session = get_session()
        
        try:
            # Get or create ticker
            ticker = session.query(Ticker).filter_by(symbol=symbol).first()
            
            if not ticker:
                ticker = Ticker(symbol=symbol, exchange="NSE")
                session.add(ticker)
                session.commit()
            
            # Add OHLCV data
            for _, row in df.iterrows():
                # Check if data already exists
                existing = session.query(OHLCV).filter_by(
                    ticker_id=ticker.id,
                    timestamp=row['timestamp'],
                    timeframe=row['timeframe']
                ).first()
                
                if not existing:
                    ohlcv = OHLCV(
                        ticker_id=ticker.id,
                        timestamp=row['timestamp'],
                        timeframe=row['timeframe'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    session.add(ohlcv)
            
            session.commit()
            logger.info(f"Saved {len(df)} bars to database for {symbol}")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving to database: {e}")
            raise
        finally:
            session.close()
    
    def fetch_and_save(
        self,
        symbol: str,
        from_date: datetime,
        to_date: datetime,
        interval: str = "day"
    ):
        """
        Fetch historical data and save to database
        
        Args:
            symbol: Trading symbol
            from_date: Start date
            to_date: End date
            interval: Timeframe
        """
        df = self.get_historical_data(symbol, from_date, to_date, interval)
        
        if not df.empty:
            self.save_to_database(df, symbol)
    
    def get_quote(self, symbols: List[str], exchange: str = "NSE") -> Dict:
        """
        Get real-time quotes for symbols
        
        Args:
            symbols: List of symbols
            exchange: Exchange
            
        Returns:
            Dictionary of quotes
        """
        self.rate_limiter.wait_if_needed()
        
        # Format symbols with exchange prefix
        formatted_symbols = [f"{exchange}:{symbol}" for symbol in symbols]
        
        quotes = self.kite.quote(formatted_symbols)
        
        logger.info(f"Fetched quotes for {len(symbols)} symbols")
        return quotes
