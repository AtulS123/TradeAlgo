"""
Data preprocessing utilities
"""

import pandas as pd
import numpy as np
from typing import Optional
from utils.logger import logger


class DataPreprocessor:
    """
    Preprocess and clean OHLCV data
    """
    
    @staticmethod
    def handle_missing_data(df: pd.DataFrame, method: str = "ffill") -> pd.DataFrame:
        """
        Handle missing data
        
        Args:
            df: DataFrame with OHLCV data
            method: Method to handle missing data (ffill, bfill, interpolate, drop)
            
        Returns:
            DataFrame with missing data handled
        """
        df = df.copy()
        
        if method == "ffill":
            df = df.fillna(method='ffill')
        elif method == "bfill":
            df = df.fillna(method='bfill')
        elif method == "interpolate":
            df = df.interpolate(method='linear')
        elif method == "drop":
            df = df.dropna()
        else:
            raise ValueError(f"Unknown method: {method}")
        
        logger.debug(f"Handled missing data using {method}")
        return df
    
    @staticmethod
    def detect_outliers(df: pd.DataFrame, column: str = "close", threshold: float = 3.0) -> pd.Series:
        """
        Detect outliers using z-score method
        
        Args:
            df: DataFrame
            column: Column to check for outliers
            threshold: Z-score threshold
            
        Returns:
            Boolean series indicating outliers
        """
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        outliers = z_scores > threshold
        
        logger.debug(f"Detected {outliers.sum()} outliers in {column}")
        return outliers
    
    @staticmethod
    def remove_outliers(df: pd.DataFrame, column: str = "close", threshold: float = 3.0) -> pd.DataFrame:
        """
        Remove outliers from data
        
        Args:
            df: DataFrame
            column: Column to check for outliers
            threshold: Z-score threshold
            
        Returns:
            DataFrame with outliers removed
        """
        outliers = DataPreprocessor.detect_outliers(df, column, threshold)
        df_clean = df[~outliers].copy()
        
        logger.info(f"Removed {outliers.sum()} outliers from {column}")
        return df_clean
    
    @staticmethod
    def resample_timeframe(df: pd.DataFrame, from_tf: str, to_tf: str) -> pd.DataFrame:
        """
        Resample data to different timeframe
        
        Args:
            df: DataFrame with OHLCV data (must have timestamp index)
            from_tf: Current timeframe
            to_tf: Target timeframe
            
        Returns:
            Resampled DataFrame
        """
        df = df.copy()
        
        # Ensure timestamp is index
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')
        
        # Map timeframe to pandas frequency
        tf_map = {
            '1minute': '1T',
            '5minute': '5T',
            '15minute': '15T',
            '30minute': '30T',
            '60minute': '60T',
            'day': 'D'
        }
        
        freq = tf_map.get(to_tf)
        if not freq:
            raise ValueError(f"Unknown timeframe: {to_tf}")
        
        # Resample
        resampled = df.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        logger.info(f"Resampled from {from_tf} to {to_tf}: {len(df)} -> {len(resampled)} bars")
        return resampled
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> bool:
        """
        Validate OHLCV data integrity
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            True if valid, False otherwise
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        
        # Check required columns
        if not all(col in df.columns for col in required_columns):
            logger.error("Missing required OHLCV columns")
            return False
        
        # Check for negative values
        if (df[required_columns] < 0).any().any():
            logger.error("Negative values found in OHLCV data")
            return False
        
        # Check high >= low
        if (df['high'] < df['low']).any():
            logger.error("High < Low found in data")
            return False
        
        # Check high >= open, close
        if ((df['high'] < df['open']) | (df['high'] < df['close'])).any():
            logger.error("High < Open/Close found in data")
            return False
        
        # Check low <= open, close
        if ((df['low'] > df['open']) | (df['low'] > df['close'])).any():
            logger.error("Low > Open/Close found in data")
            return False
        
        logger.debug("OHLCV data validation passed")
        return True
    
    @staticmethod
    def add_returns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add return columns to DataFrame
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with return columns added
        """
        df = df.copy()
        
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        return df
    
    @staticmethod
    def normalize(df: pd.DataFrame, columns: list, method: str = "minmax") -> pd.DataFrame:
        """
        Normalize data
        
        Args:
            df: DataFrame
            columns: Columns to normalize
            method: Normalization method (minmax, zscore)
            
        Returns:
            DataFrame with normalized columns
        """
        df = df.copy()
        
        for col in columns:
            if method == "minmax":
                df[f"{col}_norm"] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
            elif method == "zscore":
                df[f"{col}_norm"] = (df[col] - df[col].mean()) / df[col].std()
            else:
                raise ValueError(f"Unknown normalization method: {method}")
        
        return df
