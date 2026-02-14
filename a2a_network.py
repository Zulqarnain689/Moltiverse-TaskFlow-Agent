import aiohttp
import asyncio
import json
from typing import Dict, Optional, List
from src.models import TradeSignal, SecurityAlert
import websockets
import time

class A2ANetwork:
    def __init__(self, local_agent_id: str, server_host="localhost", server_port=8765):
        self.local_agent_id = local_agent_id
        self.server_url = f"ws://{server_host}:{server_port}"
        self.websocket = None
        self.is_connected = False
        self.message_handlers = {}
        self.sent_messages = []
        self.received_messages = []
    
    async def connect_to_server(self):
        """Connect to local A2A server"""
        try:
            print(f"🔌 Connecting to A2A server: {self.server_url}")
            self.websocket = await websockets.connect(self.server_url)
            self.is_connected = True
            print("✅ Connected to A2A network!")
            
            handshake = {
                "type": "handshake",
                "source": self.local_agent_id,
                "timestamp": time.time()
            }
            await self.websocket.send(json.dumps(handshake))
            
            asyncio.create_task(self.listen_for_messages())
            
            return True
            
        except Exception as e:
            print(f"❌ A2A connection failed: {e}")
            print("💡 Make sure local A2A server is running: python local_a2a_server.py")
            return False
    
    async def listen_for_messages(self):
        """Listen for messages from A2A network"""
        try:
            async for message in self.websocket:
                await self.process_incoming_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("🔗 A2A connection closed")
            self.is_connected = False
    
    async def process_incoming_message(self, message_json: str):
        """Process incoming A2A message"""
        try:
            data = json.loads(message_json)
            self.received_messages.append(data)
            
            msg_type = data.get("type")
            print(f"📨 A2A RX: {msg_type} from {data.get('source', 'unknown')}")
            
            if msg_type == "trade_signal":
                await self.handle_trade_signal(data)
            elif msg_type == "security_alert":
                await self.handle_security_alert(data)
            elif msg_type == "market_data_response":
                await self.handle_market_data_response(data)
            elif msg_type == "handshake_response":
                print("🤝 A2A handshake confirmed")
            
        except json.JSONDecodeError:
            print("⚠️  Invalid JSON in A2A message")
        except Exception as e:
            print(f"❌ Error processing A2A message: {e}")
    
    async def send_message(self, message: Dict):
        """Send message to A2A network"""
        if not self.is_connected or not self.websocket:
            print("⚠️  Not connected to A2A network")
            return False
        
        try:
            message["source"] = self.local_agent_id
            message["timestamp"] = time.time()
            
            await self.websocket.send(json.dumps(message))
            self.sent_messages.append(message)
            print(f"📤 A2A TX: {message['type']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send A2A message: {e}")
            return False
    
    async def broadcast_trade_signal(self, signal: TradeSignal):
        """Broadcast trade signal to network"""
        message = {
            "type": "trade_signal",
            "payload": {
                "id": signal.id,
                "pair": signal.pair,
                "direction": signal.direction,
                "amount": signal.amount,
                "price": signal.price,
                "confidence": signal.confidence,
                "risk_level": signal.risk_level
            }
        }
        return await self.send_message(message)
    
    async def request_market_data(self, pair: str) -> Optional[Dict]:
        """Request market data from network"""
        message = {
            "type": "market_data_request",
            "payload": {"pair": pair}
        }
        
        success = await self.send_message(message)
        if success:
            return {"status": "request_sent", "pair": pair}
        return None
    
    async def broadcast_security_alert(self, alert: SecurityAlert):
        """Broadcast security alert to network"""
        message = {
            "type": "security_alert",
            "payload": {
                "id": alert.id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "affected_pairs": alert.affected_pairs,
                "description": alert.description,
                "related_tx_hashes": alert.related_tx_hashes
            }
        }
        return await self.send_message(message)
    
    async def handle_trade_signal(self, data: Dict):
        """Handle incoming trade signal"""
        payload = data.get("payload", {})
        print(f"📈 Trade signal received: {payload.get('pair')} {payload.get('direction')} @ {payload.get('price')}")
    
    async def handle_security_alert(self, data: Dict):
        """Handle incoming security alert"""
        payload = data.get("payload", {})
        print(f"🚨 Security alert: {payload.get('alert_type')} - {payload.get('description')}")
    
    async def handle_market_data_response(self, data: Dict):
        """Handle market data response"""
        print(f"📊 Market data received: {data.get('pair')} - ${data.get('price')}")
