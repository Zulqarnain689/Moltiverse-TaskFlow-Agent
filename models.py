from dataclasses import dataclass
from typing import List, Optional, Dict
from enum import Enum

class TaskCategory(Enum):
    WORK = "work"
    PERSONAL = "personal"
    HEALTH = "health"
    FINANCE = "finance"
    BLOCKCHAIN = "blockchain"
    SOCIAL = "social"

@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: int
    category: str
    due_datetime: Optional[str] = None
    estimated_duration: int = 30
    reasoning_chain: str = ""
    conflicts: List[str] = None
    status: str = "pending"
    blockchain_metadata: Optional[Dict] = None
    created_at: str = ""
