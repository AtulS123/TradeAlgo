"""
Indicator library manager
"""

from typing import Dict, List, Callable, Any
import pandas as pd
from utils.logger import logger

# Import all indicators
from indicators import trend, momentum, volatility, volume


class IndicatorLibrary:
    """
    Central registry and manager for all technical indicators
    """
    
    def __init__(self):
        self.indicators: Dict[str, Dict[str, Any]] = {}
        self._register_all_indicators()
    
    def _register_all_indicators(self):
        """Register all available indicators"""
        
        # Trend Indicators
        self.register("SMA", trend.SMA, "Trend", "Simple Moving Average")
        self.register("EMA", trend.EMA, "Trend", "Exponential Moving Average")
        self.register("DEMA", trend.DEMA, "Trend", "Double Exponential Moving Average")
        self.register("HMA", trend.HMA, "Trend", "Hull Moving Average")
        self.register("MACD", trend.MACD, "Trend", "Moving Average Convergence Divergence")
        self.register("ADX", trend.ADX, "Trend", "Average Directional Index")
        self.register("Supertrend", trend.Supertrend, "Trend", "Supertrend Indicator")
        self.register("ParabolicSAR", trend.ParabolicSAR, "Trend", "Parabolic SAR")
        self.register("Aroon", trend.Aroon, "Trend", "Aroon Indicator")
        self.register("IchimokuCloud", trend.IchimokuCloud, "Trend", "Ichimoku Cloud")
        self.register("LinearRegression", trend.LinearRegression, "Trend", "Linear Regression")
        
        # Momentum Indicators
        self.register("RSI", momentum.RSI, "Momentum", "Relative Strength Index")
        self.register("Stochastic", momentum.Stochastic, "Momentum", "Stochastic Oscillator")
        self.register("WilliamsR", momentum.WilliamsR, "Momentum", "Williams %R")
        self.register("ROC", momentum.ROC, "Momentum", "Rate of Change")
        self.register("CCI", momentum.CCI, "Momentum", "Commodity Channel Index")
        self.register("MFI", momentum.MFI, "Momentum", "Money Flow Index")
        self.register("UltimateOscillator", momentum.UltimateOscillator, "Momentum", "Ultimate Oscillator")
        self.register("TSI", momentum.TSI, "Momentum", "True Strength Index")
        self.register("KST", momentum.KST, "Momentum", "Know Sure Thing")
        self.register("AwesomeOscillator", momentum.AwesomeOscillator, "Momentum", "Awesome Oscillator")
        self.register("ChandeMomentumOscillator", momentum.ChandeMomentumOscillator, "Momentum", "Chande Momentum Oscillator")
        self.register("DetrendedPriceOscillator", momentum.DetrendedPriceOscillator, "Momentum", "Detrended Price Oscillator")
        self.register("PPO", momentum.PPO, "Momentum", "Percentage Price Oscillator")
        self.register("RelativeVigorIndex", momentum.RelativeVigorIndex, "Momentum", "Relative Vigor Index")
        self.register("SchaffTrendCycle", momentum.SchaffTrendCycle, "Momentum", "Schaff Trend Cycle")
        
        # Volatility Indicators
        self.register("BollingerBands", volatility.BollingerBands, "Volatility", "Bollinger Bands")
        self.register("ATR", volatility.ATR, "Volatility", "Average True Range")
        self.register("KeltnerChannels", volatility.KeltnerChannels, "Volatility", "Keltner Channels")
        self.register("DonchianChannels", volatility.DonchianChannels, "Volatility", "Donchian Channels")
        self.register("StandardDeviation", volatility.StandardDeviation, "Volatility", "Standard Deviation")
        self.register("HistoricalVolatility", volatility.HistoricalVolatility, "Volatility", "Historical Volatility")
        self.register("ChaikinVolatility", volatility.ChaikinVolatility, "Volatility", "Chaikin Volatility")
        self.register("MassIndex", volatility.MassIndex, "Volatility", "Mass Index")
        self.register("UlcerIndex", volatility.UlcerIndex, "Volatility", "Ulcer Index")
        self.register("TrueRange", volatility.TrueRange, "Volatility", "True Range")
        
        # Volume Indicators
        self.register("VolumeMA", volume.VolumeMA, "Volume", "Volume Moving Average")
        self.register("OBV", volume.OBV, "Volume", "On-Balance Volume")
        self.register("VWAP", volume.VWAP, "Volume", "Volume Weighted Average Price")
        self.register("VolumeProfile", volume.VolumeProfile, "Volume", "Volume Profile")
        self.register("AccumulationDistribution", volume.AccumulationDistribution, "Volume", "Accumulation/Distribution Line")
        self.register("ChaikinMoneyFlow", volume.ChaikinMoneyFlow, "Volume", "Chaikin Money Flow")
        self.register("EaseOfMovement", volume.EaseOfMovement, "Volume", "Ease of Movement")
        self.register("ForceIndex", volume.ForceIndex, "Volume", "Force Index")
        self.register("KlingerOscillator", volume.KlingerOscillator, "Volume", "Klinger Oscillator")
        self.register("NegativeVolumeIndex", volume.NegativeVolumeIndex, "Volume", "Negative Volume Index")
        self.register("PositiveVolumeIndex", volume.PositiveVolumeIndex, "Volume", "Positive Volume Index")
        
        logger.info(f"Registered {len(self.indicators)} indicators")
    
    def register(self, name: str, function: Callable, category: str, description: str):
        """
        Register an indicator
        
        Args:
            name: Indicator name
            function: Indicator function
            category: Category (Trend, Momentum, Volatility, Volume)
            description: Description
        """
        self.indicators[name] = {
            'function': function,
            'category': category,
            'description': description
        }
    
    def get_indicator(self, name: str) -> Callable:
        """Get indicator function by name"""
        if name not in self.indicators:
            raise ValueError(f"Indicator '{name}' not found")
        
        return self.indicators[name]['function']
    
    def list_indicators(self, category: str = None) -> List[str]:
        """
        List all indicators or by category
        
        Args:
            category: Optional category filter
            
        Returns:
            List of indicator names
        """
        if category:
            return [name for name, info in self.indicators.items() if info['category'] == category]
        return list(self.indicators.keys())
    
    def get_categories(self) -> List[str]:
        """Get all indicator categories"""
        return list(set(info['category'] for info in self.indicators.values()))
    
    def search(self, query: str) -> List[str]:
        """
        Search indicators by name or description
        
        Args:
            query: Search query
            
        Returns:
            List of matching indicator names
        """
        query = query.lower()
        matches = []
        
        for name, info in self.indicators.items():
            if query in name.lower() or query in info['description'].lower():
                matches.append(name)
        
        return matches
    
    def get_info(self, name: str) -> Dict[str, Any]:
        """Get full information about an indicator"""
        if name not in self.indicators:
            raise ValueError(f"Indicator '{name}' not found")
        
        return {
            'name': name,
            **self.indicators[name]
        }
    
    def calculate(self, name: str, *args, **kwargs):
        """
        Calculate indicator
        
        Args:
            name: Indicator name
            *args: Positional arguments for indicator
            **kwargs: Keyword arguments for indicator
            
        Returns:
            Indicator values
        """
        func = self.get_indicator(name)
        return func(*args, **kwargs)


# Global indicator library instance
indicator_library = IndicatorLibrary()
