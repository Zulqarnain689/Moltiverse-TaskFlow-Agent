import sqlite3
import json
import uuid
from datetime import datetime
from typing import Dict, List

class DatabaseManager:
    def __init__(self, db_path: str = "moltiverse_agent.db"):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize SQLite database with blockchain metadata support"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table with blockchain integration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                priority INTEGER,
                category TEXT,
                due_datetime TEXT,
                estimated_duration INTEGER,
                reasoning_chain TEXT,
                conflicts TEXT,
                status TEXT DEFAULT 'pending',
                blockchain_metadata TEXT,
                created_at TEXT
            )
        ''')
        
        # Blockchain interactions log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blockchain_interactions (
                id TEXT PRIMARY KEY,
                interaction_type TEXT,
                contract_address TEXT,
                transaction_hash TEXT,
                block_number INTEGER,
                timestamp TEXT,
                metadata TEXT
            )
        ''')
        
        # User profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_task_to_db(self, task: 'Task'):  # Forward reference
        """Save task with blockchain metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            (id, title, description, priority, category, due_datetime, 
             estimated_duration, reasoning_chain, conflicts, status, 
             blockchain_metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id, task.title, task.description, task.priority, task.category,
            task.due_datetime, task.estimated_duration, task.reasoning_chain,
            json.dumps(task.conflicts) if task.conflicts else None,
            task.status,
            json.dumps(task.blockchain_metadata) if task.blockchain_metadata else None,
            task.created_at
        ))
        
        conn.commit()
        conn.close()
    
    def log_blockchain_interaction(self, interaction_type: str, metadata: Dict, 
                                 contract_address: str = None, transaction_hash: str = None):
        """Log blockchain interactions for audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO blockchain_interactions 
            (id, interaction_type, contract_address, transaction_hash, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            f"bc_{uuid.uuid4()}",
            interaction_type,
            contract_address,
            transaction_hash,
            json.dumps(metadata),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def load_persistent_state(self):
        """Load tasks and user profile from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Load tasks
        cursor.execute("SELECT * FROM tasks WHERE status != 'completed'")
        rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            from src.models import Task
            task = Task(
                id=row[0], title=row[1], description=row[2], 
                priority=row[3], category=row[4], due_datetime=row[5],
                estimated_duration=row[6], reasoning_chain=row[7],
                conflicts=json.loads(row[8]) if row[8] else [], status=row[9],
                blockchain_metadata=json.loads(row[10]) if row[10] else None,
                created_at=row[11]
            )
            tasks.append(task)
        
        # Load user profile
        cursor.execute("SELECT key, value FROM user_profile")
        profile_rows = cursor.fetchall()
        user_profile = {}
        for key, value in profile_rows:
            try:
                user_profile[key] = json.loads(value)
            except:
                user_profile[key] = value
        
        conn.close()
        return tasks, user_profile
