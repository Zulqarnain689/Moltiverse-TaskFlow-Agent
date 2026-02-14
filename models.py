from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class TradeSignal:
    id: str
    pair: str  # e.g., "ETH/MONAD"
    direction: str  # "BUY" or "SELL"
    amount: float
    price: float
    confidence: float  # 0.0 to 1.0
    timestamp: str
    source_agent: str
    risk_level: str  # "low", "medium", "high"
    metadata: Dict[str, Any]

@dataclass
class SecurityAlert:
    id: str
    alert_type: str  # "flash_crash", "anomaly", "front_run", "manipulation"
    severity: int  # 1-10
    affected_pairs: List[str]
    description: str
    timestamp: str
    related_tx_hashes: List[str]
    resolved: bool = False

@dataclass
class MarketDataPoint:
    pair: str
    price: float
    volume: float
    timestamp: str
    liquidity: float
    volatility: float
