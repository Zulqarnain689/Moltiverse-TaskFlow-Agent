import asyncio
import aiohttp
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import asdict
from src.models import Task
from src.blockchain_utils import BlockchainConnector
from src.database import DatabaseManager

class MoltiverseTaskFlowAssistant:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.blockchain = BlockchainConnector(
            rpc_endpoint=os.getenv("MONAD_RPC_URL", "https://rpc.nad.fun"),
            wallet_address=os.getenv("MONAD_WALLET_ADDRESS")
        )
        
        # Load persistent state
        self.tasks, self.user_profile = self.db_manager.load_persistent_state()
        
        # Initialize AI model
        self.ai_model_type = os.getenv("AI_MODEL_TYPE", "gemini")
        self.initialize_ai_client()
        
        self.current_session_id = str(uuid.uuid4())
        self.waiting_for_confirmation = False
        self.pending_resolution = None
    
    def initialize_ai_client(self):
        """Initialize AI client based on hackathon requirements"""
        if self.ai_model_type == "gemini":
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            self.ai_call = self.call_gemini_api
        elif self.ai_model_type == "openai":
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            self.ai_call = self.call_openai_api
        else:
            raise ValueError(f"Unsupported AI model type: {self.ai_model_type}")
    
    async def call_gemini_api(self, prompt: str) -> Dict:
        """Gemini API call with hackathon compliance"""
        if not self.gemini_api_key:
            return {"error": "GEMINI_API_KEY not configured"}
        
        headers = {'Content-Type': 'application/json'}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 1000}
        }
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={self.gemini_api_key}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(gemini_url, headers=headers, json=data) as response:
                    result = await response.json()
                    if 'candidates' in result and len(result['candidates']) > 0:
                        text_response = result['candidates'][0]['content']['parts'][0]['text']
                        try:
                            return json.loads(text_response)
                        except:
                            return {"response": text_response}
            except Exception as e:
                return {"error": str(e)}
    
    async def extract_entities_semantically(self, text: str) -> Dict:
        """Enhanced semantic extraction with blockchain context"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        blockchain_context = ""
        if any(word in text.lower() for word in ['wallet', 'crypto', 'token', 'monad', 'blockchain']):
            blockchain_context = "\nConsider this request might involve blockchain interactions."
        
        prompt = f"""
        Current time: {current_time}
        {blockchain_context}
        
        Analyze this user request and extract structured information:
        "{text}"
        
        Return ONLY a JSON object with these exact keys:
        {{
            "action": "the main action/task",
            "time_context": "specific time mentioned or 'relative'",
            "date_context": "specific date mentioned or 'relative'",
            "urgency_indicators": ["list of urgency words/phrases"],
            "dependencies": ["list of dependent actions"],
            "resources_needed": ["list of resources mentioned"],
            "blockchain_related": true/false
        }}
        """
        
        result = await self.ai_call(prompt)
        return result if isinstance(result, dict) and 'error' not in result else {
            'action': text,
            'time_context': 'unknown',
            'date_context': 'unknown',
            'urgency_indicators': [],
            'dependencies': [],
            'resources_needed': [],
            'blockchain_related': False
        }
    
    async def resolve_relative_time(self, time_context: str, date_context: str) -> Optional[str]:
        """Convert relative time expressions to absolute datetime"""
        current_time = datetime.now()
        
        if 'now' in time_context.lower() or 'immediately' in time_context.lower():
            return current_time.isoformat()
        
        if 'tomorrow' in date_context.lower():
            target_date = current_time + timedelta(days=1)
            return target_date.isoformat()
        
        if 'next week' in date_context.lower():
            target_date = current_time + timedelta(days=7)
            return target_date.isoformat()
        
        # Use AI for complex relative time resolution
        prompt = f"""
        Current time: {current_time.strftime("%Y-%m-%d %H:%M:%S")}
        Time context: {time_context}
        Date context: {date_context}
        
        Convert these relative time expressions to an ISO format datetime string.
        If impossible to determine, return null.
        Respond ONLY with the ISO datetime string or null.
        """
        
        result = await self.ai_call(prompt)
        if isinstance(result, dict) and 'response' in result:
            response_text = result['response'].strip()
            if response_text.lower() == 'null':
                return None
            try:
                parsed_time = datetime.fromisoformat(response_text.replace('Z', '+00:00'))
                return parsed_time.isoformat()
            except:
                return None
        return None
    
    def calculate_buffer_time_conflicts(self, new_task: Task) -> List[Dict]:
        """Advanced conflict detection including buffer times"""
        conflicts = []
        
        if not new_task.due_datetime:
            return conflicts
        
        new_start = datetime.fromisoformat(new_task.due_datetime)
        new_end = new_start + timedelta(minutes=new_task.estimated_duration)
        
        for existing_task in self.tasks:
            if not existing_task.due_datetime or existing_task.id == new_task.id:
                continue
            
            existing_start = datetime.fromisoformat(existing_task.due_datetime)
            existing_end = existing_start + timedelta(minutes=existing_task.estimated_duration)
            
            buffer_minutes = 10
            new_end_with_buffer = new_end + timedelta(minutes=buffer_minutes)
            existing_end_with_buffer = existing_end + timedelta(minutes=buffer_minutes)
            
            if (new_start < existing_end_with_buffer and new_end_with_buffer > existing_start):
                conflict_info = {
                    'task1': new_task.title,
                    'task2': existing_task.title,
                    'type': 'hard_conflict' if (new_start < existing_end and new_end > existing_start) else 'buffer_conflict',
                    'severity': 'high' if 'hard_conflict' else 'medium',
                    'recommended_buffer': buffer_minutes
                }
                conflicts.append(conflict_info)
        
        return conflicts
    
    async def external_blockchain_connector(self, task: Task) -> Optional[Dict]:
        """Enhanced external connector with blockchain integration"""
        blockchain_data = {}
        
        if task.category.upper() in ["FINANCE", "BLOCKCHAIN"]:
            if self.blockchain.wallet_address:
                balance = await self.blockchain.check_wallet_balance()
                if balance is not None:
                    blockchain_data["wallet_balance"] = balance
                    blockchain_data["balance_check_timestamp"] = datetime.now().isoformat()
            
            gas_price = await self.blockchain.get_gas_price()
            if gas_price:
                blockchain_data["current_gas_price"] = gas_price
                blockchain_data["gas_price_timestamp"] = datetime.now().isoformat()
        
        if blockchain_data:
            self.db_manager.log_blockchain_interaction(
                interaction_type="read_operation",
                metadata={
                    "task_id": task.id,
                    "task_category": task.category,
                    "data_fetched": list(blockchain_data.keys())
                }
            )
        
        return blockchain_data if blockchain_data else None
    
    async def process_complete_workflow(self, user_input: str) -> Dict:
        """Complete workflow with blockchain integration"""
        current_time = datetime.now().isoformat()
        
        # Step 1: Semantic understanding
        entities = await self.extract_entities_semantically(user_input)
        
        # Step 2: Resolve relative time
        resolved_time = await self.resolve_relative_time(
            entities.get('time_context', ''),
            entities.get('date_context', '')
        )
        
        # Step 3: Generate reasoning chain
        reasoning = f"LLM extracted: {entities} | Time resolved: {resolved_time}"
        
        # Step 4: Create task
        new_task = Task(
            id=f"task_{uuid.uuid4()}",
            title=entities.get('action', user_input)[:100],
            description=user_input,
            priority=len(entities.get('urgency_indicators', [])) * 2 + 1,
            category=entities.get('action', 'PERSONAL').upper(),
            due_datetime=resolved_time,
            estimated_duration=30,
            reasoning_chain=reasoning,
            created_at=current_time
        )
        
        # Step 5: Blockchain integration check
        blockchain_data = await self.external_blockchain_connector(new_task)
        if blockchain_data:
            new_task.blockchain_metadata = blockchain_data
            new_task.reasoning_chain += f" | Blockchain data: {list(blockchain_data.keys())}"
        
        # Step 6: Check for conflicts
        conflicts = self.calculate_buffer_time_conflicts(new_task)
        
        if conflicts:
            resolution_result = await self.handle_multi_turn_dialogue(conflicts, new_task)
            if resolution_result["action"] == "wait_for_confirmation":
                return resolution_result
        
        # Step 7: Save to persistent storage
        self.tasks.append(new_task)
        self.db_manager.save_task_to_db(new_task)
        
        # Step 8: Update user profile
        self.user_profile["last_interaction"] = current_time
        self.save_user_profile()
        
        return {
            "task_created": asdict(new_task),
            "conflicts_found": len(conflicts),
            "blockchain_integration": bool(blockchain_data),
            "blockchain_data_keys": list(blockchain_data.keys()) if blockchain_data else []
        }
    
    def save_user_profile(self):
        """Save user profile to database"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        for key, value in self.user_profile.items():
            cursor.execute(
                "INSERT OR REPLACE INTO user_profile (key, value) VALUES (?, ?)",
                (key, json.dumps(value))
            )
        
        conn.commit()
        conn.close()
    
    async def handle_multi_turn_dialogue(self, conflicts: List[Dict], new_task: Task) -> Dict:
        """Handle multi-turn conversation for conflict resolution"""
        if not conflicts:
            return {"action": "proceed", "task": new_task}
        
        self.waiting_for_confirmation = True
        self.pending_resolution = {
            "conflicts": conflicts,
            "new_task": new_task,
            "options": []
        }
        
        options = []
        for i, conflict in enumerate(conflicts):
            option = {
                "id": f"option_{i}",
                "description": f"Move {conflict['task2']} to avoid conflict with {new_task.title}",
                "action": "move_existing",
                "target_task": conflict['task2']
            }
            options.append(option)
        
        options.append({
            "id": "option_new",
            "description": f"Reschedule {new_task.title} to avoid conflicts",
            "action": "move_new",
            "target_task": new_task.title
        })
        
        self.pending_resolution["options"] = options
        
        return {
            "action": "wait_for_confirmation",
            "message": f"Found {len(conflicts)} conflicts. Choose resolution:",
            "options": options,
            "conflicts_details": conflicts
        }
    
    async def proactive_nudging_loop(self):
        """Enhanced proactive monitoring with blockchain awareness"""
        while True:
            current_time = datetime.now()
            
            # Check for upcoming tasks
            upcoming_tasks = [
                task for task in self.tasks 
                if task.due_datetime and 
                datetime.fromisoformat(task.due_datetime) <= current_time + timedelta(minutes=30) and
                task.status == "pending"
            ]
            
            if upcoming_tasks:
                print(f"\n🔔 PROACTIVE ALERT: {len(upcoming_tasks)} tasks coming up!")
                for task in upcoming_tasks:
                    blockchain_indicator = "🔗" if task.blockchain_metadata else "📝"
                    print(f"   {blockchain_indicator} {task.title} at {task.due_datetime}")
            
            # Periodic blockchain health check
            if current_time.second % 30 == 0:
                gas_price = await self.blockchain.get_gas_price()
                if gas_price:
                    print(f"⛽ Monad Gas Price: {gas_price} wei")
            
            await asyncio.sleep(5)
