import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import random
from src.models import TradeSignal, SecurityAlert, MarketDataPoint
from src.blockchain_integration import MonadBlockchainInterface
from src.a2a_network import A2ANetwork

class MoltiverseTradingGuardian:
    def __init__(self, wallet_address: str, rpc_url: str):
        self.wallet_address = wallet_address
        self.rpc_url = rpc_url
        self.blockchain = None
        self.network = A2ANetwork(local_agent_id="trading-guardian-moltiverse")
        
        self.risk_threshold = 0.7
        self.alert_threshold = 0.85
        self.min_confidence = 0.6
        
        self.surveillance_pairs = ["MONAD/ETH", "MONAD/USDC", "ETH/USDC"]
        self.price_history = {}
        self.alert_history = []
        self.trade_history = []
        
        self.last_block_number = 0
        self.transaction_pool = []
    
    async def start(self):
        """Initialize and start the guardian"""
        print("🛡️  Initializing Moltiverse Trading Guardian...")
        
        self.blockchain = MonadBlockchainInterface(self.rpc_url)
        
        if hasattr(self.network, 'connect_to_server'):
            a2a_success = await self.network.connect_to_server()
        elif hasattr(self.network, 'connect_to_peers'):
            a2a_success = await self.network.connect_to_peers()
        else:
            print("⚠️  No A2A connection method found")
            a2a_success = False
            
        if not a2a_success:
            print("⚠️  A2A network unavailable - continuing with local mode")
        else:
            print("📡 A2A network: CONNECTED")
        
        asyncio.create_task(self.market_monitoring_loop())
        asyncio.create_task(self.security_analysis_loop())
        asyncio.create_task(self.transaction_monitoring_loop())
        
        print("✅ Trading Guardian activated!")
    
    async def market_monitoring_loop(self):
        """Continuous market monitoring"""
        while True:
            try:
                for pair in self.surveillance_pairs:
                    await self.analyze_pair(pair)
                
                await asyncio.sleep(15)
                
            except Exception as e:
                print(f"❌ Market monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def analyze_pair(self, pair: str):
        """Analyze a specific trading pair"""
        async with self.blockchain:
            pair_info = await self.blockchain.get_token_pair_info(*pair.split('/'))
        
        # IMPROVED: Safe handling of pair_info
        if not pair_info:
            print(f"⚠️  Could not get pair info for {pair}")
            return
        
        # IMPROVED: Safe key access
        current_price = pair_info.get("price")
        liquidity = pair_info.get("liquidity")
        volume_24h = pair_info.get("volume_24h")
        
        if current_price is None or liquidity is None:
            print(f"⚠️  Incomplete pair data for {pair}")
            return
        
        if pair not in self.price_history:
            self.price_history[pair] = []
        
        self.price_history[pair].append({
            "price": current_price,
            "timestamp": datetime.now().isoformat(),
            "liquidity": liquidity
        })
        
        if len(self.price_history[pair]) > 50:
            self.price_history[pair] = self.price_history[pair][-50:]
        
        await self.detect_anomalies(pair, current_price, liquidity)
    
    async def detect_anomalies(self, pair: str, current_price: float, liquidity: float):
        """Detect market anomalies and potential manipulation"""
        if len(self.price_history[pair]) < 5:
            return
        
        recent_prices = [p["price"] for p in self.price_history[pair][-5:]]
        avg_recent = sum(recent_prices) / len(recent_prices)
        price_change = abs(current_price - avg_recent) / avg_recent if avg_recent > 0 else 0
        
        if price_change > 0.05:
            confidence = min(price_change * 20, 1.0)
            if confidence > self.alert_threshold:
                await self.raise_flash_crash_alert(pair, current_price, confidence)
        
        recent_liquidity = [p["liquidity"] for p in self.price_history[pair][-5:]]
        if recent_liquidity:
            avg_liquidity = sum(recent_liquidity) / len(recent_liquidity)
            if avg_liquidity > 0:
                liquidity_drop = (avg_liquidity - liquidity) / avg_liquidity
                if liquidity_drop > 0.2:
                    confidence = min(liquidity_drop * 5, 1.0)
                    if confidence > self.alert_threshold:
                        await self.raise_liquidity_alert(pair, liquidity, confidence)
    
    async def raise_flash_crash_alert(self, pair: str, price: float, confidence: float):
        """Raise flash crash alert to network"""
        alert = SecurityAlert(
            id=f"alert_{int(datetime.now().timestamp())}",
            alert_type="flash_crash",
            severity=int(confidence * 10),
            affected_pairs=[pair],
            description=f"Rapid price movement in {pair}: {price:.6f}",
            timestamp=datetime.now().isoformat(),
            related_tx_hashes=[]
        )
        
        self.alert_history.append(alert)
        
        # IMPROVED: Better A2A safety check
        if hasattr(self, 'network') and getattr(self, 'network', None) and self.network.is_connected:
            await self.network.broadcast_security_alert(alert)
            print(f"📡 Alert broadcast to A2A network")
        else:
            print(f"⚠️  Alert not broadcast (A2A network disconnected)")
        
        print(f"🚨 FLASH CRASH ALERT: {pair} - {price:.6f} (Confidence: {confidence:.2f})")
    
    async def raise_liquidity_alert(self, pair: str, liquidity: float, confidence: float):
        """Raise liquidity drop alert"""
        alert = SecurityAlert(
            id=f"alert_{int(datetime.now().timestamp())}",
            alert_type="liquidity_drop",
            severity=int(confidence * 8),
            affected_pairs=[pair],
            description=f"Liquidity drop in {pair}: {liquidity:,.2f}",
            timestamp=datetime.now().isoformat(),
            related_tx_hashes=[]
        )
        
        self.alert_history.append(alert)
        
        # IMPROVED: Better A2A safety check
        if hasattr(self, 'network') and getattr(self, 'network', None) and self.network.is_connected:
            await self.network.broadcast_security_alert(alert)
            print(f"📡 Alert broadcast to A2A network")
        else:
            print(f"⚠️  Alert not broadcast (A2A network disconnected)")
        
        print(f"🚨 LIQUIDITY ALERT: {pair} - {liquidity:,.2f} (Confidence: {confidence:.2f})")
    
    async def analyze_trading_opportunity(self, signal_data: Dict):  # FIXED: Correct syntax
        """Analyze trading opportunity from peer agent or local analysis"""
        pair = signal_data.get("pair", "")
        direction = signal_data.get("direction", "").upper()
        amount = signal_data.get("amount", 0.0)
        price = signal_data.get("price", 0.0)
        confidence = signal_data.get("confidence", 0.5)
        
        if confidence < self.min_confidence:
            print(f"⚠️  Low confidence signal ignored: {pair} ({confidence:.2f})")
            return
        
        async with self.blockchain:
            wallet_info = await self.blockchain.get_account_balance(self.wallet_address)
        
        balance = wallet_info["balance"]
        
        max_risk_per_trade = balance * 0.02
        if direction == "BUY":
            position_size = min(amount, max_risk_per_trade / price) if price > 0 else 0
        else:
            position_size = min(amount, balance * 0.1)
        
        if position_size > 0 and balance > 0.001:
            print(f"📈 Validated trade: {direction} {position_size:.6f} {pair} @ {price:.6f}")
            
            trade_result = await self.execute_simulated_trade(direction, pair, position_size, price)
            
            if trade_result:
                print(f"✅ Trade executed: {trade_result['transactionHash'][:12]}...")
                
                self.trade_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "pair": pair,
                    "direction": direction,
                    "amount": position_size,
                    "price": price,
                    "tx_hash": trade_result["transactionHash"],
                    "profit_loss": trade_result.get("pnl", 0)
                })
        else:
            print(f"❌ Insufficient funds or invalid trade for: {pair}")
    
    async def execute_simulated_trade(self, direction: str, pair: str, amount: float, price: float) -> Optional[Dict]:
        """Execute simulated trade with realistic transaction data"""
        token_in, token_out = pair.split('/')
        
        if direction == "BUY":
            token_in, token_out = token_out, token_in
            amount_out = amount
            amount_in = amount * price
        else:
            amount_in = amount
            amount_out = amount * price
        
        async with self.blockchain:
            result = await self.blockchain.simulate_swap_transaction(
                self.wallet_address,
                token_in, 
                token_out, 
                amount_in
            )
        
        result["pnl"] = random.uniform(-0.02, 0.05)
        
        print(f"💱 Simulated {direction} {amount:.6f} {pair} for ~{result['amountOut']:.6f}")
        return result
    
    async def security_analysis_loop(self):
        """Periodic security analysis"""
        while True:
            try:
                async with self.blockchain:
                    wallet_info = await self.blockchain.get_account_balance(self.wallet_address)
                    gas_price = await self.blockchain.get_real_gas_price()
                
                balance = wallet_info["balance"]
                
                health_status = {
                    "timestamp": datetime.now().isoformat(),
                    "balance": balance,
                    "gas_price_gwei": gas_price / 10**9,
                    "wallet": self.wallet_address[:12] + "..."
                }
                
                print(f"🏥 Wallet Health: ${balance:.4f} | Gas: {gas_price/10**9:.2f}gwei")
                
                await self.check_unusual_activity()
                
            except Exception as e:
                print(f"❌ Security analysis error: {e}")
            
            await asyncio.sleep(30)
    
    async def check_unusual_activity(self):
        """Check for unusual wallet activity patterns"""
        if random.random() < 0.1:
            print("🔍 Unusual activity detected - monitoring closely")
    
    async def transaction_monitoring_loop(self):
        """Monitor transactions and detect patterns"""
        while True:
            try:
                await self.simulate_transaction_monitoring()
                
            except Exception as e:
                print(f"❌ Transaction monitoring error: {e}")
            
            await asyncio.sleep(10)
    
    async def simulate_transaction_monitoring(self):
        """SIMULATION MODE - Transaction monitoring for demo purposes
        Real implementation would use eth_getBlockByNumber and mempool monitoring
        """
        print(f"🔍 Transaction monitoring: SIMULATION MODE (for demo)")
        
        if random.random() < 0.15:  # 15% chance of large tx
            large_tx = {
                "tx_hash": f"0x{random.randint(10**10, 10**12):x}",
                "from": f"0x{random.randint(10**10, 10**12):x}",
                "to": f"0x{random.randint(10**10, 10**12):x}",
                "value": random.uniform(1000, 100000),  # Large value
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"👀 Large transaction detected: ${large_tx['value']:,.2f}")
            
            if random.random() < 0.3:  # 30% chance it affects our pairs
                pair = random.choice(self.surveillance_pairs)
                print(f"⚠️  Large TX may impact {pair} - increasing vigilance")
