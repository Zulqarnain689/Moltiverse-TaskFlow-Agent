import asyncio
import websockets
import json
import threading
from typing import Dict, List
from datetime import datetime

class LocalA2AServer:
    def __init__(self):
        self.clients = set()
        self.agent_registry = {}
        self.message_history = []
    
    async def register_client(self, websocket, path):
        """Register a new client connection"""
        self.clients.add(websocket)
        print(f"🔗 New A2A client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"🔗 Client disconnected: {websocket.remote_address}")
        finally:
            self.clients.remove(websocket)
    
    async def handle_message(self, websocket, message):
        """Handle incoming A2A message"""
        try:
            data = json.loads(message)
            print(f"📨 A2A Message: {data['type']} from {data.get('source', 'unknown')}")
            
            self.message_history.append({
                "message": data,
                "received_at": datetime.now().isoformat(),
                "source": data.get("source")
            })
            
            response = await self.process_message(data)
            if response:
                await websocket.send(json.dumps(response))
                
        except json.JSONDecodeError:
            error_msg = {
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(error_msg))
    
    async def process_message(self, data: Dict):
        """Process different types of A2A messages"""
        msg_type = data.get("type")
        
        if msg_type == "handshake":
            return {
                "type": "handshake_response",
                "status": "connected",
                "capabilities": ["trade_signals", "security_alerts", "market_data"],
                "timestamp": datetime.now().isoformat()
            }
        
        elif msg_type == "trade_signal":
            print(f"📈 Received trade signal: {data.get('payload', {}).get('pair')} - {data.get('payload', {}).get('direction')}")
            await self.broadcast_to_agents(data, exclude_source=data.get("source"))
            
            return {
                "type": "trade_signal_ack",
                "status": "received",
                "signal_id": data.get("payload", {}).get("id"),
                "timestamp": datetime.now().isoformat()
            }
        
        elif msg_type == "security_alert":
            print(f"🚨 Security alert: {data.get('payload', {}).get('alert_type')}")
            await self.broadcast_to_agents(data, exclude_source=data.get("source"))
            
            return {
                "type": "security_alert_ack",
                "status": "received",
                "alert_id": data.get("payload", {}).get("id"),
                "timestamp": datetime.now().isoformat()
            }
        
        elif msg_type == "market_data_request":
            pair = data.get("payload", {}).get("pair", "MONAD/ETH")
            import random
            response = {
                "type": "market_data_response",
                "pair": pair,
                "price": random.uniform(1.0, 100.0),
                "liquidity": random.uniform(100000, 10000000),
                "volume_24h": random.uniform(50000, 5000000),
                "timestamp": datetime.now().isoformat()
            }
            return response
        
        return None
    
    async def broadcast_to_agents(self, message: Dict, exclude_source: str = None):
        """Broadcast message to all connected agents"""
        if not self.clients:
            return
        
        message["broadcast"] = True
        message["broadcast_timestamp"] = datetime.now().isoformat()
        
        disconnected_clients = []
        for client in self.clients.copy():
            try:
                if exclude_source and message.get("source") == exclude_source:
                    continue
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
        
        for client in disconnected_clients:
            self.clients.discard(client)
    
    async def start_server(self, host="localhost", port=8765):
        """START SERVER ASYNC"""
        server = await websockets.serve(self.register_client, host, port)
        print(f"📡 A2A Server started on ws://{host}:{port}")
        await server.wait_closed()

def start_local_server():
    """Thread-safe server starter"""
    server = LocalA2AServer()
    asyncio.run(server.start_server("localhost", 8765))
