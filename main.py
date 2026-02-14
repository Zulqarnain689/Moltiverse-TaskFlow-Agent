import asyncio
import os
import threading
import uuid
from datetime import datetime
from src.trading_guardian import MoltiverseTradingGuardian
from src.local_a2a_server import LocalA2AServer
from src.models import TradeSignal

def start_local_server():
    """Start the local A2A server in background"""
    server = LocalA2AServer()
    asyncio.run(server.start_server("localhost", 8765))

async def main():
    print("🛡️  Moltiverse Trading Guardian Agent")
    print("=" * 50)
    
    server_thread = threading.Thread(target=start_local_server, daemon=True)
    server_thread.start()
    
    await asyncio.sleep(2)
    
    wallet_address = os.getenv("MONAD_WALLET_ADDRESS", "0x1234567890123456789012345678901234567890")
    rpc_url = os.getenv("MONAD_RPC_URL", "https://rpc.nad.fun")
    
    print(f"💳 Wallet: {wallet_address[:8]}...")
    print(f"🔗 RPC: {rpc_url}")
    print()
    
    guardian = MoltiverseTradingGuardian(wallet_address, rpc_url)
    
    await guardian.start()
    
    print("\n🎯 Guardian Status:")
    print("   • Market surveillance: ACTIVE")
    print("   • Security monitoring: ACTIVE") 
    print(f"   • A2A network: {'CONNECTED' if guardian.network.is_connected else 'LOCAL MODE'}")  # IMPROVED: Conditional status
    print("   • Transaction monitoring: ACTIVE")
    print("   • Risk management: ENABLED")
    
    print(f"\n📊 Starting market analysis...")
    await asyncio.sleep(5)
    
    demo_signal_obj = TradeSignal(
        id=str(uuid.uuid4()),
        pair="MONAD/ETH",
        direction="BUY",
        amount=100.0,
        price=0.0012,
        confidence=0.8,
        timestamp=datetime.now().isoformat(),
        source_agent="demo",
        risk_level="medium",
        metadata={}
    )
    
    print(f"\n📈 Analyzing demo trade opportunity...")
    await guardian.analyze_trading_opportunity(demo_signal_obj.__dict__)
    
    try:
        print(f"\n📡 Guardian running... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print(f"\n🛑 Guardian shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
