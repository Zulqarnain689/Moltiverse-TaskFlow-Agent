import aiohttp
import uuid
from typing import Dict, Optional, List

class BlockchainConnector:
    def __init__(self, rpc_endpoint: str, wallet_address: str = None):
        self.rpc_endpoint = rpc_endpoint
        self.wallet_address = wallet_address
    
    async def call_monad_blockchain_read(self, method: str, params: List = None) -> Dict:
        """Perform read operations on Monad blockchain"""
        if not params:
            params = []
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": str(uuid.uuid4())[:8]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.rpc_endpoint, json=payload) as response:
                    result = await response.json()
                    return result
        except Exception as e:
            print(f"Blockchain read error: {e}")
            return {"error": str(e), "result": None}
    
    async def check_wallet_balance(self, address: str = None) -> Optional[float]:
        """Check Monad wallet balance - on-chain functionality"""
        target_address = address or self.wallet_address
        
        if not target_address:
            return None
        
        result = await self.call_monad_blockchain_read(
            "eth_getBalance", 
            [target_address, "latest"]
        )
        
        if "result" in result and result["result"]:
            balance_hex = result["result"]
            balance_wei = int(balance_hex, 16)
            balance_eth = balance_wei / 10**18
            return round(balance_eth, 6)
        
        return None
    
    async def get_gas_price(self) -> Optional[int]:
        """Get current gas price from Monad network"""
        result = await self.call_monad_blockchain_read("eth_gasPrice")
        
        if "result" in result and result["result"]:
            gas_price_hex = result["result"]
            return int(gas_price_hex, 16)
        
        return None
