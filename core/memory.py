import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import logger

class AgentMemory:
    """
    Lite memory using JSON files (ChromaDB alternative for Windows).
    """
    
    def __init__(self, storage_dir: str = "./memory"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        self.plans_file = os.path.join(storage_dir, "successful_plans.json")
        self.errors_file = os.path.join(storage_dir, "error_lessons.json")
        self.cache_file = os.path.join(storage_dir, "cache.json")
        
        self._load_data()
        logger.info("🧠 Lite Memory initialized")
    
    def _load_data(self):
        for file_path in [self.plans_file, self.errors_file, self.cache_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump([], f)
    
    def _read_json(self, file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _write_json(self, file_path: str, data: List[Dict]):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def store_successful_plan(self, query: str, plan: Dict, result_summary: str):
        """Store successful plan."""
        plans = self._read_json(self.plans_file)
        plans.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "plan": plan,
            "result_summary": str(result_summary)[:500],
            "query_type": self._categorize_query(query)
        })
        # Keep only last 50
        self._write_json(self.plans_file, plans[-50:])
    
    def retrieve_similar_plans(self, query: str, n_results: int = 3) -> List[Dict]:
        """Retrieve similar past queries using simple matching."""
        plans = self._read_json(self.plans_file)
        if not plans:
            return []
        
        query_words = set(query.lower().split())
        if not query_words:
            return []
        
        scored = []
        for idx, plan in enumerate(plans):
            if not isinstance(plan, dict) or "query" not in plan:
                continue
            
            plan_words = set(plan["query"].lower().split())
            # Calculate similarity score
            common = len(query_words & plan_words)
            total = len(query_words)
            score = common / total if total > 0 else 0
            
            if score > 0.3:  # Threshold
                # Store as tuple (negative_score for descending, index to avoid dict comparison)
                scored.append((-score, idx, plan))
        
        # Sort by score descending (negative ascending)
        scored.sort()
        
        # Return top n_results
        results = []
        for neg_score, idx, plan in scored[:n_results]:
            results.append({
                "past_query": plan["query"],
                "plan_used": plan.get("plan", {}),
                "similarity_score": -neg_score,
                "past_result": plan.get("result_summary", "")
            })
        
        return results
    
    def store_error_correction(self, query: str, error: str, correction: str):
        """Store error lessons."""
        errors = self._read_json(self.errors_file)
        errors.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "error_type": self._classify_error(error),
            "correction": correction
        })
        self._write_json(self.errors_file, errors[-30:])
    
    def get_error_lessons(self, query: str, error_type: Optional[str] = None) -> List[str]:
        """Get past error lessons."""
        errors = self._read_json(self.errors_file)
        lessons = []
        for e in errors:
            if error_type is None or e.get("error_type") == error_type:
                lessons.append(e.get("correction", ""))
        return lessons[-5:]
    
    def cache_result(self, cache_key: str, result: Any, ttl_hours: int = 24):
        """Cache results."""
        cache = self._read_json(self.cache_file)
        cache.append({
            "key": cache_key,
            "result": result,
            "expires": datetime.now().timestamp() + (ttl_hours * 3600)
        })
        # Clean expired
        now = datetime.now().timestamp()
        cache = [c for c in cache if c.get("expires", 0) > now]
        self._write_json(self.cache_file, cache[-100:])
    
    def get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result."""
        cache = self._read_json(self.cache_file)
        now = datetime.now().timestamp()
        for entry in cache:
            if entry.get("key") == cache_key and entry.get("expires", 0) > now:
                logger.info("⚡ Cache hit!")
                return entry.get("result")
        return None
    
    def _categorize_query(self, query: str) -> str:
        query_lower = query.lower()
        if any(x in query_lower for x in ["weather", "temperature"]):
            return "weather"
        elif any(x in query_lower for x in ["github", "repo"]):
            return "github"
        elif any(x in query_lower for x in ["news", "latest"]):
            return "news"
        else:
            return "general"
    
    def _classify_error(self, error: str) -> str:
        error_lower = str(error).lower()
        if "api" in error_lower:
            return "api_failure"
        elif "timeout" in error_lower:
            return "network"
        return "unknown"

# Global instance
memory = AgentMemory()