"""
Market Regime Engine

Uses Hidden Markov Models (HMM) to classify market states into:
1. Bull Quiet
2. Bull Volatile
3. Bear Quiet
4. Bear Volatile
5. Sideways

Input: Sector Index Data (OHLC)
Output: Regime ID for each timestamp
"""

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from typing import Tuple

class RegimeEngine:
    def __init__(self, n_states: int = 4):
        self.n_states = n_states
        self.model = GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100, random_state=42)
        self.is_fitted = False
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features for HMM:
        1. Returns (Log Returns)
        2. Volatility (Rolling Std Dev / ATR)
        3. Trend Strength (ADX)
        """
        data = df.copy()
        
        # 1. Log Returns
        data['log_ret'] = np.log(data['close'] / data['close'].shift(1))
        
        # 2. Volatility (Range)
        data['range'] = (data['high'] - data['low']) / data['close']
        
        # 3. Trend (ADX) - Optional, can add noise if not careful
        # adx = ta.adx(data['high'], data['low'], data['close'], length=14)
        # data['adx'] = adx['ADX_14']
        
        data.dropna(inplace=True)
        return data[['log_ret', 'range']]

    def train(self, df: pd.DataFrame):
        """Fit the HMM model on historical data"""
        features = self.prepare_features(df)
        X = features.values
        
        self.model.fit(X)
        self.is_fitted = True
        
        # Analyze states to label them (Bull/Bear/Volatile)
        # We need to map the hidden states (0,1,2,3) to human readable regimes
        # This is done by looking at the Mean Returns and Variance of each state
        means = self.model.means_
        covars = self.model.covars_
        
        # Logic to map states:
        # High Return + Low Var = Bull Quiet
        # High Return + High Var = Bull Volatile
        # Low Return + Low Var = Bear Quiet (or Sideways)
        # Low Return + High Var = Bear Volatile
        
        # For now, we just store the model. The mapping happens in prediction or analysis.
        
    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Predict regime for new data"""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call train() first.")
            
        features = self.prepare_features(df)
        hidden_states = self.model.predict(features.values)
        
        return pd.Series(hidden_states, index=features.index, name='regime')

    def get_regime_map(self) -> dict:
        """
        Returns a dictionary mapping State ID -> Description
        This requires heuristic analysis of the trained model means/vars.
        """
        if not self.is_fitted:
            return {}
            
        map_dict = {}
        for i in range(self.n_states):
            mean_ret = self.model.means_[i][0]
            volatility = np.sqrt(np.diag(self.model.covars_[i]))[0] # Approx
            
            if mean_ret > 0 and volatility < 0.01:
                desc = "Bull Quiet"
            elif mean_ret > 0 and volatility >= 0.01:
                desc = "Bull Volatile"
            elif mean_ret < 0 and volatility >= 0.01:
                desc = "Bear Volatile"
            else:
                desc = "Sideways/Bear Quiet"
            
            map_dict[i] = desc
            
        return map_dict
