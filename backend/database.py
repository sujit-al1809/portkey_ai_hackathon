"""
Database setup and operations for Cost-Quality Optimization System
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path(__file__).parent / "data" / "optimization.db"

def init_db():
    """Initialize database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Prompts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            use_case TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Model completions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            completion TEXT NOT NULL,
            tokens_input INTEGER,
            tokens_output INTEGER,
            latency_ms INTEGER,
            cost REAL,
            success BOOLEAN,
            is_refusal BOOLEAN DEFAULT 0,
            error TEXT,
            retry_count INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prompt_id) REFERENCES prompts(prompt_id)
        )
    """)
    
    # Quality evaluations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quality_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            overall_score INTEGER,
            accuracy INTEGER,
            helpfulness INTEGER,
            clarity INTEGER,
            completeness INTEGER,
            reasoning TEXT,
            evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prompt_id) REFERENCES prompts(prompt_id)
        )
    """)
    
    # Optimization recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_model TEXT NOT NULL,
            recommended_model TEXT NOT NULL,
            cost_reduction_percent REAL,
            quality_impact_percent REAL,
            avg_quality_loss REAL,
            cost_quality_ratio REAL,
            use_case TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")


def save_prompt(prompt_id: str, content: str, use_case: str = "general"):
    """Save a prompt to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO prompts (prompt_id, content, use_case)
        VALUES (?, ?, ?)
    """, (prompt_id, content, use_case))
    
    conn.commit()
    conn.close()


def save_completion(prompt_id: str, model_name: str, result: Dict[str, Any]):
    """Save a model completion to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO completions (
            prompt_id, model_name, completion, tokens_input, tokens_output,
            latency_ms, cost, success, is_refusal, error, retry_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt_id,
        model_name,
        result.get("completion", ""),
        result.get("tokens_input", 0),
        result.get("tokens_output", 0),
        result.get("latency_ms", 0),
        result.get("cost", 0.0),
        result.get("success", False),
        result.get("is_refusal", False),
        result.get("error"),
        result.get("retry_count", 0)
    ))
    
    conn.commit()
    conn.close()


def save_quality_evaluation(prompt_id: str, model_name: str, evaluation: Dict[str, Any]):
    """Save quality evaluation to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    scores = evaluation.get("dimension_scores", {})
    
    cursor.execute("""
        INSERT INTO quality_evaluations (
            prompt_id, model_name, overall_score, accuracy, helpfulness,
            clarity, completeness, reasoning
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt_id,
        model_name,
        evaluation.get("overall_score", 0),
        scores.get("accuracy", 0),
        scores.get("helpfulness", 0),
        scores.get("clarity", 0),
        scores.get("completeness", 0),
        evaluation.get("reasoning", "")
    ))
    
    conn.commit()
    conn.close()


def save_recommendation(recommendation: Dict[str, Any]):
    """Save optimization recommendation to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO recommendations (
            current_model, recommended_model, cost_reduction_percent,
            quality_impact_percent, avg_quality_loss, cost_quality_ratio, use_case
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        recommendation.get("current_model", ""),
        recommendation.get("recommended_model", ""),
        recommendation.get("cost_reduction_percent", 0.0),
        recommendation.get("quality_impact_percent", 0.0),
        recommendation.get("avg_quality_loss", 0.0),
        recommendation.get("cost_quality_ratio", 0.0),
        recommendation.get("use_case", "general")
    ))
    
    conn.commit()
    conn.close()


def get_dashboard_data() -> Dict[str, Any]:
    """Get all data for dashboard display"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get total prompts tested
    cursor.execute("SELECT COUNT(DISTINCT prompt_id) as count FROM prompts")
    total_prompts = cursor.fetchone()["count"]
    
    # Get total completions
    cursor.execute("SELECT COUNT(*) as count FROM completions WHERE success = 1")
    total_completions = cursor.fetchone()["count"]
    
    # Get refusal rates by model
    cursor.execute("""
        SELECT model_name, 
               COUNT(*) as total,
               SUM(CASE WHEN is_refusal = 1 THEN 1 ELSE 0 END) as refusals,
               SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failures
        FROM completions
        GROUP BY model_name
    """)
    model_reliability = {row["model_name"]: {
        "total": row["total"],
        "refusals": row["refusals"] or 0,
        "failures": row["failures"] or 0,
        "refusal_rate": (row["refusals"] or 0) / row["total"] * 100 if row["total"] > 0 else 0,
        "success_rate": (row["total"] - (row["failures"] or 0)) / row["total"] * 100 if row["total"] > 0 else 0
    } for row in cursor.fetchall()}
    
    # Get average quality scores by model
    cursor.execute("""
        SELECT model_name, AVG(overall_score) as avg_score, COUNT(*) as count
        FROM quality_evaluations
        GROUP BY model_name
    """)
    model_quality = {row["model_name"]: {
        "avg_score": row["avg_score"],
        "count": row["count"]
    } for row in cursor.fetchall()}
    
    # Get total cost by model
    cursor.execute("""
        SELECT model_name, SUM(cost) as total_cost, AVG(latency_ms) as avg_latency
        FROM completions
        WHERE success = 1
        GROUP BY model_name
    """)
    model_costs = {row["model_name"]: {
        "total_cost": row["total_cost"],
        "avg_latency": row["avg_latency"]
    } for row in cursor.fetchall()}
    
    # Get recent recommendations
    cursor.execute("""
        SELECT * FROM recommendations
        ORDER BY created_at DESC
        LIMIT 10
    """)
    recommendations = [dict(row) for row in cursor.fetchall()]
    
    # Get recent prompts with completions
    cursor.execute("""
        SELECT p.prompt_id, p.content, p.use_case, p.created_at,
               GROUP_CONCAT(c.model_name) as models_tested
        FROM prompts p
        LEFT JOIN completions c ON p.prompt_id = c.prompt_id
        GROUP BY p.prompt_id
        ORDER BY p.created_at DESC
        LIMIT 20
    """)
    recent_prompts = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "total_prompts": total_prompts,
        "total_completions": total_completions,
        "model_quality": model_quality,
        "model_costs": model_costs,
        "model_reliability": model_reliability,
        "recommendations": recommendations,
        "recent_prompts": recent_prompts
    }


def get_prompt_details(prompt_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed results for a specific prompt"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get prompt info
    cursor.execute("SELECT * FROM prompts WHERE prompt_id = ?", (prompt_id,))
    prompt = cursor.fetchone()
    if not prompt:
        conn.close()
        return None
    
    # Get completions
    cursor.execute("""
        SELECT * FROM completions WHERE prompt_id = ?
        ORDER BY timestamp DESC
    """, (prompt_id,))
    completions = [dict(row) for row in cursor.fetchall()]
    
    # Get quality evaluations
    cursor.execute("""
        SELECT * FROM quality_evaluations WHERE prompt_id = ?
        ORDER BY evaluated_at DESC
    """, (prompt_id,))
    evaluations = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "prompt": dict(prompt),
        "completions": completions,
        "evaluations": evaluations
    }


if __name__ == "__main__":
    # Initialize database
    init_db()
    print("Database setup complete!")
