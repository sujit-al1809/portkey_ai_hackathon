"""
Cache Manager - State management with versioning and invalidation rules
Supports caching of model outputs, evaluations, and recommendations
"""
import json
import hashlib
import sqlite3
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

DB_PATH = Path(__file__).parent / "data" / "optimization.db"


class CacheKeys:
    """Cache key prefixes"""
    MODEL_OUTPUT = "model_output"
    EVALUATION = "evaluation"
    RECOMMENDATION = "recommendation"
    PRICING = "pricing"
    REGISTRY = "registry"


@dataclass
class CacheEntry:
    """A cached item with metadata"""
    key: str
    value: Any
    created_at: str
    expires_at: str
    version: str
    source_versions: Dict[str, str]  # e.g., {"model_registry": "1.0.0", "pricing": "2024-01"}


class CacheManager:
    """
    Production cache manager with:
    - TTL-based expiration
    - Version-based invalidation
    - Source tracking
    """
    
    def __init__(self):
        self.registry_version = "1.0.0"
        self.pricing_version = "2024-01"
        self.rubric_version = "1.0.0"
        self._init_db()
    
    def _init_db(self):
        """Initialize cache tables"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                version TEXT NOT NULL,
                source_versions_json TEXT,
                hit_count INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_invalidation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invalidation_type TEXT NOT NULL,
                affected_keys INTEGER,
                reason TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def generate_key(self, prefix: str, **kwargs) -> str:
        """Generate a unique cache key from components"""
        components = [prefix] + [f"{k}={v}" for k, v in sorted(kwargs.items())]
        key_string = ":".join(components)
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    def get(self, key: str) -> Optional[Any]:
        """Get a cached value if valid"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cache WHERE cache_key = ?", (key,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Check expiration
        expires_at = datetime.fromisoformat(row["expires_at"])
        if datetime.utcnow() > expires_at:
            cursor.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            return None
        
        # Check version compatibility
        source_versions = json.loads(row["source_versions_json"]) if row["source_versions_json"] else {}
        if not self._versions_compatible(source_versions):
            cursor.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
            conn.commit()
            conn.close()
            return None
        
        # Update hit count
        cursor.execute("UPDATE cache SET hit_count = hit_count + 1 WHERE cache_key = ?", (key,))
        conn.commit()
        conn.close()
        
        return json.loads(row["value_json"])
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Set a cached value with TTL"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=ttl_seconds)
        
        source_versions = {
            "model_registry": self.registry_version,
            "pricing": self.pricing_version,
            "rubric": self.rubric_version
        }
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO cache (
                    cache_key, value_json, created_at, expires_at, 
                    version, source_versions_json, hit_count
                ) VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (
                key,
                json.dumps(value, default=str),
                now.isoformat(),
                expires_at.isoformat(),
                "1.0.0",
                json.dumps(source_versions)
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
        finally:
            conn.close()
    
    def invalidate(self, key: str) -> bool:
        """Invalidate a specific cache entry"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM cache WHERE cache_key = ?", (key,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def invalidate_by_prefix(self, prefix: str) -> int:
        """Invalidate all entries matching a prefix pattern"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get matching keys (we use hash so need to track separately)
        # For now, invalidate all
        cursor.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM cache")
        conn.commit()
        
        # Log invalidation
        cursor.execute("""
            INSERT INTO cache_invalidation_log (
                invalidation_type, affected_keys, reason, timestamp
            ) VALUES (?, ?, ?, ?)
        """, (
            "prefix_invalidation",
            count,
            f"Prefix: {prefix}",
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        conn.close()
        
        return count
    
    def invalidate_on_version_change(self, component: str, new_version: str) -> int:
        """Invalidate cache when a component version changes"""
        old_version = None
        
        if component == "model_registry":
            old_version = self.registry_version
            self.registry_version = new_version
        elif component == "pricing":
            old_version = self.pricing_version
            self.pricing_version = new_version
        elif component == "rubric":
            old_version = self.rubric_version
            self.rubric_version = new_version
        
        if old_version and old_version != new_version:
            return self.invalidate_by_prefix(component)
        
        return 0
    
    def _versions_compatible(self, source_versions: Dict[str, str]) -> bool:
        """Check if cached entry's source versions are still current"""
        if source_versions.get("model_registry") != self.registry_version:
            return False
        if source_versions.get("pricing") != self.pricing_version:
            return False
        if source_versions.get("rubric") != self.rubric_version:
            return False
        return True
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), SUM(hit_count) FROM cache")
        row = cursor.fetchone()
        total_entries = row[0] or 0
        total_hits = row[1] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM cache 
            WHERE expires_at > ?
        """, (datetime.utcnow().isoformat(),))
        valid_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "total_hits": total_hits,
            "registry_version": self.registry_version,
            "pricing_version": self.pricing_version,
            "rubric_version": self.rubric_version
        }
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM cache WHERE expires_at < ?
        """, (datetime.utcnow().isoformat(),))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted


# Global instance
cache_manager = CacheManager()


# ============================================================================
# CONVERSATION HASH CACHE
# ============================================================================
class ConversationCache:
    """
    Specialized cache for conversation/prompt hashing
    Prevents re-running same tests
    """
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_cache (
                conversation_hash TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                run_version TEXT NOT NULL,
                output_json TEXT NOT NULL,
                quality_score REAL,
                cost REAL,
                latency_ms REAL,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def hash_conversation(self, messages: List[Dict]) -> str:
        """Generate deterministic hash for conversation"""
        content = json.dumps(messages, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_cached_output(self, conversation_hash: str, model_id: str) -> Optional[Dict]:
        """Get cached output for a conversation+model pair"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM conversation_cache 
            WHERE conversation_hash = ? AND model_id = ?
        """, (conversation_hash, model_id))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "output": json.loads(row["output_json"]),
                "quality_score": row["quality_score"],
                "cost": row["cost"],
                "latency_ms": row["latency_ms"],
                "run_version": row["run_version"],
                "created_at": row["created_at"]
            }
        
        return None
    
    def cache_output(self, conversation_hash: str, model_id: str,
                    output: Any, quality_score: float,
                    cost: float, latency_ms: float,
                    run_version: str = "1.0.0"):
        """Cache a conversation output"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO conversation_cache (
                conversation_hash, model_id, run_version,
                output_json, quality_score, cost, latency_ms, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conversation_hash,
            model_id,
            run_version,
            json.dumps(output, default=str),
            quality_score,
            cost,
            latency_ms,
            datetime.utcnow().isoformat()
        ))
        
        conn.commit()
        conn.close()


# Global instance
conversation_cache = ConversationCache()


if __name__ == "__main__":
    print("Testing Cache Manager")
    print("=" * 40)
    
    # Test basic operations
    key = cache_manager.generate_key("test", model="gpt-4", prompt_hash="abc123")
    print(f"Generated key: {key}")
    
    cache_manager.set(key, {"test": "data"}, ttl_seconds=60)
    print(f"Set value: {cache_manager.get(key)}")
    
    print(f"\nCache stats: {cache_manager.get_stats()}")
