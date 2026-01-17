"""
User Session and Historical Chat Management
Simple username-based login with conversation history
"""
import json
import sqlite3
import hashlib
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "optimization.db"


@dataclass
class SessionData:
    """User session information"""
    session_id: str
    username: str
    user_id: str
    created_at: str
    last_activity: str
    is_active: bool


@dataclass
class HistoricalChat:
    """Stored conversation from history"""
    chat_id: str
    user_id: str
    question: str
    response: str
    model_used: str
    quality_score: float
    cost: float
    created_at: str
    similarity_score: float = 0.0  # For matching


class SessionManager:
    """Manage user sessions and login"""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize session tables"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Historical chats per user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historical_chats (
                chat_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                question TEXT NOT NULL,
                question_embedding TEXT,
                response TEXT NOT NULL,
                model_used TEXT NOT NULL,
                quality_score REAL,
                cost REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES sessions(user_id)
            )
        """)
        
        # Chat similarity index for faster matching
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                question_hash TEXT NOT NULL,
                user_id TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES historical_chats(chat_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def login(self, username: str) -> SessionData:
        """
        Simple username login (no password for hackathon).
        Creates session and returns user's historical data.
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT * FROM sessions WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        if row:
            # Existing user - update last activity
            session_id = row["session_id"]
            user_id = row["user_id"]
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                UPDATE sessions 
                SET last_activity = ?, is_active = 1
                WHERE session_id = ?
            """, (now, session_id))
            
        else:
            # New user - create session
            user_id = self._generate_user_id(username)
            session_id = self._generate_session_id(username)
            now = datetime.utcnow().isoformat()
            
            cursor.execute("""
                INSERT INTO sessions 
                (session_id, username, user_id, created_at, last_activity)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, username, user_id, now, now))
        
        conn.commit()
        
        # Retrieve session data before closing
        cursor.execute("SELECT * FROM sessions WHERE username = ?", (username,))
        row = cursor.fetchone()
        
        conn.close()
        
        return SessionData(
            session_id=row["session_id"],
            username=row["username"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            last_activity=row["last_activity"],
            is_active=bool(row["is_active"])
        )
    
    def logout(self, session_id: str):
        """Mark session as inactive"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE sessions SET is_active = 0 WHERE session_id = ?
        """, (session_id,))
        
        conn.commit()
        conn.close()
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get active session"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions WHERE session_id = ? AND is_active = 1
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return SessionData(
            session_id=row["session_id"],
            username=row["username"],
            user_id=row["user_id"],
            created_at=row["created_at"],
            last_activity=row["last_activity"],
            is_active=bool(row["is_active"])
        )
    
    def _generate_session_id(self, username: str) -> str:
        """Generate unique session ID"""
        content = f"{username}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    def _generate_user_id(self, username: str) -> str:
        """Generate user ID from username"""
        return hashlib.sha256(username.encode()).hexdigest()[:16]


class HistoricalChatManager:
    """Manage user's conversation history"""
    
    def __init__(self):
        pass
    
    def save_chat(self, user_id: str, question: str, response: str,
                 model_used: str, quality_score: float, cost: float) -> str:
        """Save a conversation to history"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        chat_id = self._generate_chat_id(user_id, question)
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO historical_chats
            (chat_id, user_id, question, response, model_used, quality_score, cost, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id, user_id, question, response, 
            model_used, quality_score, cost, now
        ))
        
        # Create index for faster similarity search
        question_hash = hashlib.md5(question.lower().encode()).hexdigest()
        cursor.execute("""
            INSERT INTO chat_index (chat_id, question_hash, user_id)
            VALUES (?, ?, ?)
        """, (chat_id, question_hash, user_id))
        
        conn.commit()
        conn.close()
        
        return chat_id
    
    def get_user_history(self, user_id: str, limit: int = 50) -> List[HistoricalChat]:
        """Get all conversations for a user"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM historical_chats 
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            HistoricalChat(
                chat_id=row["chat_id"],
                user_id=row["user_id"],
                question=row["question"],
                response=row["response"],
                model_used=row["model_used"],
                quality_score=row["quality_score"],
                cost=row["cost"],
                created_at=row["created_at"]
            )
            for row in rows
        ]
    
    def find_similar_question(self, user_id: str, question: str, 
                             similarity_threshold: float = 0.8) -> Optional[HistoricalChat]:
        """
        Find if user asked similar question before.
        Uses simple text similarity (can upgrade to embeddings).
        """
        history = self.get_user_history(user_id, limit=100)
        
        if not history:
            return None
        
        best_match = None
        best_score = 0.0
        
        for chat in history:
            # Simple similarity: word overlap
            score = self._calculate_similarity(question, chat.question)
            
            if score > best_score and score >= similarity_threshold:
                best_score = score
                best_match = chat
                best_match.similarity_score = score
        
        return best_match
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1) using improved algorithm"""
        import re
        
        # Normalize text
        text1_clean = re.sub(r'[^a-z0-9\s]', '', text1.lower())
        text2_clean = re.sub(r'[^a-z0-9\s]', '', text2.lower())
        
        # Common stop words to ignore
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'be', 'by', 'do', 'i', 'my', 'me', 'you', 'your'}
        
        # Get significant words (non-stop words, len > 2)
        words1 = set(w for w in text1_clean.split() if w not in stop_words and len(w) > 2)
        words2 = set(w for w in text2_clean.split() if w not in stop_words and len(w) > 2)
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate intersection and union
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        # Jaccard similarity on significant words
        jaccard = intersection / union if union > 0 else 0.0
        
        # Also check for common substrings (n-grams)
        # Extract 2-3 character n-grams
        def get_ngrams(text, n=3):
            text = text.replace(' ', '')
            return set(text[i:i+n] for i in range(len(text) - n + 1))
        
        ngrams1 = get_ngrams(text1_clean)
        ngrams2 = get_ngrams(text2_clean)
        
        if ngrams1 and ngrams2:
            ngram_score = len(ngrams1 & ngrams2) / len(ngrams1 | ngrams2) if ngrams1 | ngrams2 else 0.0
        else:
            ngram_score = 0.0
        
        # Combined score: 70% word overlap, 30% n-gram overlap
        return 0.7 * jaccard + 0.3 * ngram_score
    
    def _generate_chat_id(self, user_id: str, question: str) -> str:
        """Generate unique chat ID"""
        content = f"{user_id}:{question}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]


# Global instances
session_manager = SessionManager()
chat_manager = HistoricalChatManager()


if __name__ == "__main__":
    print("Testing Session Manager")
    print("=" * 50)
    
    # Test login
    print("\n1. Login user 'alice'")
    session = session_manager.login("alice")
    print(f"   Session ID: {session.session_id}")
    print(f"   User ID: {session.user_id}")
    
    # Save a chat
    print("\n2. Save conversation to history")
    chat_id = chat_manager.save_chat(
        user_id=session.user_id,
        question="Write a Python function to sort a list",
        response="def sort_list(lst):\n    return sorted(lst)",
        model_used="GPT-4o-mini",
        quality_score=92.0,
        cost=0.0001
    )
    print(f"   Chat saved: {chat_id}")
    
    # Get history
    print("\n3. Retrieve user history")
    history = chat_manager.get_user_history(session.user_id)
    print(f"   Total chats: {len(history)}")
    for chat in history:
        print(f"   - {chat.question[:50]}...")
    
    # Find similar question
    print("\n4. Check if similar question exists")
    similar = chat_manager.find_similar_question(
        session.user_id,
        "How do I create a function to sort an array in Python?"
    )
    if similar:
        print(f"   Found similar: {similar.question}")
        print(f"   Similarity: {similar.similarity_score:.1%}")
        print(f"   Can reuse response from: {similar.model_used}")
    else:
        print("   No similar question found")
    
    # Logout
    print("\n5. Logout")
    session_manager.logout(session.session_id)
    print("   Session closed")
    
    # Login again
    print("\n6. Login again (should retrieve same user)")
    session2 = session_manager.login("alice")
    print(f"   Same User ID: {session2.user_id == session.user_id}")
