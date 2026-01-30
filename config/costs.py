"""
Transaction Cost Model for Indian Markets (Zerodha 2025)

This module implements a precise cost model including:
1. Brokerage (Zerodha rates)
2. STT (Securities Transaction Tax - Oct 2024 rates)
3. Exchange Transaction Charges (NSE)
4. SEBI Charges
5. Stamp Duty
6. GST
7. Slippage Model based on Market Cap
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

class InstrumentType(Enum):
    EQUITY_DELIVERY = "EQUITY_DELIVERY"
    EQUITY_INTRADAY = "EQUITY_INTRADAY"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"

class MarketCap(Enum):
    NIFTY50 = "NIFTY50"      # Large Cap / High Liquidity
    MIDCAP = "MIDCAP"        # Mid Cap
    SMALLCAP = "SMALLCAP"    # Small Cap / Low Liquidity

@dataclass
class TradeCost:
    brokerage: float
    stt: float
    exchange_txn: float
    sebi_charges: float
    stamp_duty: float
    gst: float
    total_tax_charges: float
    slippage: float
    net_pnl: float

class CostModel:
    # Tax Rates (Oct 2024)
    STT_RATES = {
        InstrumentType.EQUITY_DELIVERY: {'buy': 0.001, 'sell': 0.001},
        InstrumentType.EQUITY_INTRADAY: {'buy': 0.0, 'sell': 0.00025},
        InstrumentType.FUTURES: {'buy': 0.0, 'sell': 0.0002},
        InstrumentType.OPTIONS: {'buy': 0.0, 'sell': 0.001} # On Premium
    }
    
    EXCHANGE_TXN_RATES = {
        InstrumentType.EQUITY_INTRADAY: 0.0000297,
        InstrumentType.EQUITY_DELIVERY: 0.0000297,
        InstrumentType.FUTURES: 0.0000173,
        InstrumentType.OPTIONS: 0.0003503 # On Premium
    }
    
    STAMP_DUTY_RATES = {
        InstrumentType.EQUITY_DELIVERY: 0.00015,
        InstrumentType.EQUITY_INTRADAY: 0.00003,
        InstrumentType.FUTURES: 0.00002,
        InstrumentType.OPTIONS: 0.00003
    }
    
    SEBI_CHARGE_RATE = 0.000001 # ₹10 per crore
    GST_RATE = 0.18
    
    # Slippage Model
    SLIPPAGE_RATES = {
        MarketCap.NIFTY50: 0.0005,   # 0.05%
        MarketCap.MIDCAP: 0.0010,    # 0.10%
        MarketCap.SMALLCAP: 0.0010   # 0.10%
    }

    @staticmethod
    def calculate_brokerage(turnover: float, instrument_type: InstrumentType) -> float:
        """Calculate Zerodha Brokerage"""
        if instrument_type == InstrumentType.EQUITY_DELIVERY:
            return 0.0
        elif instrument_type == InstrumentType.EQUITY_INTRADAY:
            return min(turnover * 0.0003, 20.0)
        else: # F&O
            return 20.0

    @classmethod
    def calculate_costs(cls, 
                       entry_price: float, 
                       exit_price: float, 
                       quantity: int, 
                       instrument_type: InstrumentType,
                       market_cap: MarketCap = MarketCap.NIFTY50,
                       is_buy_first: bool = True) -> TradeCost:
        """
        Calculate all costs and net P&L for a complete trade (Entry + Exit).
        """
        
        # 1. Apply Slippage to Prices
        slippage_pct = cls.SLIPPAGE_RATES[market_cap]
        
        if is_buy_first: # Long Trade
            real_entry = entry_price * (1 + slippage_pct) # Buy higher
            real_exit = exit_price * (1 - slippage_pct)   # Sell lower
        else: # Short Trade
            real_entry = entry_price * (1 - slippage_pct) # Sell lower
            real_exit = exit_price * (1 + slippage_pct)   # Buy higher
            
        gross_pnl = (real_exit - real_entry) * quantity if is_buy_first else (real_entry - real_exit) * quantity
        slippage_cost = abs(gross_pnl - ((exit_price - entry_price) * quantity if is_buy_first else (entry_price - exit_price) * quantity))

        # Turnover Calculation
        buy_price = real_entry if is_buy_first else real_exit
        sell_price = real_exit if is_buy_first else real_entry
        
        buy_turnover = buy_price * quantity
        sell_turnover = sell_price * quantity
        total_turnover = buy_turnover + sell_turnover
        
        # 2. Brokerage (Charged on both legs)
        brokerage = cls.calculate_brokerage(buy_turnover, instrument_type) + \
                    cls.calculate_brokerage(sell_turnover, instrument_type)
        
        # 3. STT (Security Transaction Tax)
        stt = (buy_turnover * cls.STT_RATES[instrument_type]['buy']) + \
              (sell_turnover * cls.STT_RATES[instrument_type]['sell'])
              
        # 4. Exchange Transaction Charges
        exchange_txn = total_turnover * cls.EXCHANGE_TXN_RATES[instrument_type]
        
        # 5. SEBI Charges
        sebi_charges = total_turnover * cls.SEBI_CHARGE_RATE
        
        # 6. Stamp Duty (Buy side only)
        stamp_duty = buy_turnover * cls.STAMP_DUTY_RATES[instrument_type]
        
        # 7. GST (18% on Brokerage + Exchange Txn + SEBI)
        gst = (brokerage + exchange_txn + sebi_charges) * cls.GST_RATE
        
        total_tax_charges = brokerage + stt + exchange_txn + sebi_charges + stamp_duty + gst
        net_pnl = gross_pnl - total_tax_charges
        
        return TradeCost(
            brokerage=round(brokerage, 2),
            stt=round(stt, 2),
            exchange_txn=round(exchange_txn, 2),
            sebi_charges=round(sebi_charges, 2),
            stamp_duty=round(stamp_duty, 2),
            gst=round(gst, 2),
            total_tax_charges=round(total_tax_charges, 2),
            slippage=round(slippage_cost, 2),
            net_pnl=round(net_pnl, 2)
        )

    @classmethod
    def get_net_pnl(cls, entry: float, exit: float, qty: int, type: InstrumentType, cap: MarketCap = MarketCap.NIFTY50) -> float:
        """Helper to get just the Net P&L"""
        cost = cls.calculate_costs(entry, exit, qty, type, cap)
        return cost.net_pnl
