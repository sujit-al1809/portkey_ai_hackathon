"""
User Metadata Service - Manages user profiles, constraints, and history
"""
import json
import hashlib
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent / "data" / "optimization.db"


@dataclass
class UserConstraints:
    """User-defined constraints for model selection"""
    max_budget_per_1k_requests: float = 10.0  # $ budget
    max_latency_ms: int = 5000
    min_quality_score: float = 80.0
    compliance_level: str = "standard"  # "strict", "standard", "relaxed"
    preferred_providers: List[str] = field(default_factory=list)
    blocked_providers: List[str] = field(default_factory=list)


@dataclass 
class UserMetadata:
    """Complete user profile for optimization"""
    user_id: str
    current_model: str
    use_case: str  # "support_bot", "extraction", "summarization", "coding", "creative", "reasoning"
    constraints: UserConstraints
    preferred_output_format: str = "text"  # "text", "json", "markdown", "code"
    avg_input_tokens: int = 500
    avg_output_tokens: int = 200
    monthly_request_volume: int = 10000
    last_n_conversations: List[Dict] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return asdict(self)


class UserMetadataService:
    """Service for managing user metadata"""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize user metadata tables"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                current_model TEXT NOT NULL,
                use_case TEXT NOT NULL,
                preferred_output_format TEXT DEFAULT 'text',
                avg_input_tokens INTEGER DEFAULT 500,
                avg_output_tokens INTEGER DEFAULT 200,
                monthly_request_volume INTEGER DEFAULT 10000,
                constraints_json TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                messages_json TEXT NOT NULL,
                model_used TEXT,
                tokens_input INTEGER,
                tokens_output INTEGER,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_user(self, metadata: UserMetadata) -> bool:
        """Create a new user profile"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO users (
                    user_id, current_model, use_case, preferred_output_format,
                    avg_input_tokens, avg_output_tokens, monthly_request_volume,
                    constraints_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.user_id,
                metadata.current_model,
                metadata.use_case,
                metadata.preferred_output_format,
                metadata.avg_input_tokens,
                metadata.avg_output_tokens,
                metadata.monthly_request_volume,
                json.dumps(asdict(metadata.constraints)),
                metadata.created_at,
                metadata.updated_at
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def get_user(self, user_id: str) -> Optional[UserMetadata]:
        """Get user metadata by ID"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Get last N conversations
        cursor.execute("""
            SELECT messages_json, model_used, tokens_input, tokens_output
            FROM user_conversations
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 20
        """, (user_id,))
        
        conversations = []
        for conv_row in cursor.fetchall():
            conversations.append({
                "messages": json.loads(conv_row["messages_json"]),
                "model_used": conv_row["model_used"],
                "tokens_input": conv_row["tokens_input"],
                "tokens_output": conv_row["tokens_output"]
            })
        
        conn.close()
        
        constraints_data = json.loads(row["constraints_json"]) if row["constraints_json"] else {}
        
        return UserMetadata(
            user_id=row["user_id"],
            current_model=row["current_model"],
            use_case=row["use_case"],
            preferred_output_format=row["preferred_output_format"],
            avg_input_tokens=row["avg_input_tokens"],
            avg_output_tokens=row["avg_output_tokens"],
            monthly_request_volume=row["monthly_request_volume"],
            constraints=UserConstraints(**constraints_data),
            last_n_conversations=conversations,
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user metadata"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key == "constraints":
                set_clauses.append("constraints_json = ?")
                values.append(json.dumps(value))
            elif key in ["current_model", "use_case", "preferred_output_format", 
                        "avg_input_tokens", "avg_output_tokens", "monthly_request_volume"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        set_clauses.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(user_id)
        
        cursor.execute(f"""
            UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?
        """, values)
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    
    def add_conversation(self, user_id: str, conversation_id: str, 
                        messages: List[Dict], model_used: str,
                        tokens_input: int, tokens_output: int):
        """Add a conversation to user history"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO user_conversations (
                user_id, conversation_id, messages_json, model_used,
                tokens_input, tokens_output, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            conversation_id,
            json.dumps(messages),
            model_used,
            tokens_input,
            tokens_output,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def get_conversation_hash(self, messages: List[Dict]) -> str:
        """Generate a hash for conversation deduplication"""
        content = json.dumps(messages, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_or_create_default_user(self, user_id: str = "default") -> UserMetadata:
        """Get or create a default user for testing"""
        user = self.get_user(user_id)
        if user:
            return user
        
        # Default user uses GPT-4o so we can recommend cheaper alternatives
        default = UserMetadata(
            user_id=user_id,
            current_model="gpt-4o",  # Start with expensive model
            use_case="general",
            constraints=UserConstraints(),
            preferred_output_format="text",
            avg_input_tokens=500,
            avg_output_tokens=200,
            monthly_request_volume=10000
        )
        self.create_user(default)
        return default


# Global instance
user_service = UserMetadataService()


if __name__ == "__main__":
    # Test user service
    user = user_service.get_or_create_default_user()
    print(f"User: {user.user_id}")
    print(f"Current model: {user.current_model}")
    print(f"Use case: {user.use_case}")
    print(f"Constraints: {asdict(user.constraints)}")
