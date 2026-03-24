import tiktoken
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class CostEntry:
    timestamp: str
    component: str  # 'planner', 'executor', 'critic', etc.
    operation: str  # 'llm_call', 'api_call', etc.
    model: Optional[str]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    details: Dict = field(default_factory=dict)


class CostTracker:
    """
    Real-time cost monitoring for the entire agent swarm.
    Tracks LLM tokens and external API costs.
    """
    
    # Pricing per 1K tokens (as of 2024)
    MODEL_PRICING = {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
    }
    
    # External API costs (approximate per call)
    API_COSTS = {
        "tavily_search": 0.005,      # $5 per 1000 searches
        "firecrawl_scrape": 0.002,   # $2 per 1000 pages
        "notion_create": 0.001,
    }
    
    def __init__(self):
        self.entries: List[CostEntry] = []
        self._encoder_cache = {}
    
    def _get_encoder(self, model: str):
        """Cache tiktoken encoders for performance."""
        if model not in self._encoder_cache:
            try:
                self._encoder_cache[model] = tiktoken.encoding_for_model(model)
            except:
                # Fallback to cl100k_base for unknown models
                self._encoder_cache[model] = tiktoken.get_encoding("cl100k_base")
        return self._encoder_cache[model]
    
    def add_llm_cost(
        self, 
        component: str, 
        model: str, 
        prompt: str, 
        completion: str,
        operation: str = "llm_call"
    ) -> float:
        """
        Calculate and store LLM API cost.
        Returns the cost of this specific call.
        """
        encoder = self._get_encoder(model)
        
        input_tokens = len(encoder.encode(prompt))
        output_tokens = len(encoder.encode(completion))
        
        # Calculate cost
        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING["gpt-3.5-turbo"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        total_cost = input_cost + output_cost
        
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            component=component,
            operation=operation,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=total_cost,
            details={"prompt_length": len(prompt), "completion_length": len(completion)}
        )
        
        self.entries.append(entry)
        return total_cost
    
    def add_api_cost(self, component: str, api_name: str, details: Dict = None) -> float:
        """Track external API costs (Tavily, Firecrawl, etc.)"""
        cost = self.API_COSTS.get(api_name, 0.001)
        
        entry = CostEntry(
            timestamp=datetime.now().isoformat(),
            component=component,
            operation="api_call",
            model=None,
            input_tokens=0,
            output_tokens=0,
            cost_usd=cost,
            details={"api": api_name, **(details or {})}
        )
        
        self.entries.append(entry)
        return cost
    
    def get_total_cost(self) -> float:
        """Get total cost in USD."""
        return sum(entry.cost_usd for entry in self.entries)
    
    def get_cost_by_component(self) -> Dict[str, float]:
        """Breakdown by agent/component."""
        breakdown = {}
        for entry in self.entries:
            breakdown[entry.component] = breakdown.get(entry.component, 0) + entry.cost_usd
        return breakdown
    
    def get_report(self) -> Dict:
        """Generate a detailed cost report."""
        total = self.get_total_cost()
        by_component = self.get_cost_by_component()
        
        return {
            "total_cost_usd": round(total, 4),
            "total_calls": len(self.entries),
            "by_component": {k: round(v, 4) for k, v in by_component.items()},
            "breakdown": [
                {
                    "time": e.timestamp,
                    "component": e.component,
                    "operation": e.operation,
                    "cost": round(e.cost_usd, 6),
                    "tokens": e.input_tokens + e.output_tokens if e.model else 0
                }
                for e in self.entries[-10:]  # Last 10 entries
            ]
        }
    
    def print_summary(self):
        """Print colorful cost summary to console."""
        report = self.get_report()
        print(f"\n{'='*50}")
        print(f"💰 COST TRACKER SUMMARY")
        print(f"{'='*50}")
        print(f"Total Spent: ${report['total_cost_usd']:.4f}")
        print(f"Total Operations: {report['total_calls']}")
        print(f"\nBreakdown by Agent:")
        for comp, cost in report['by_component'].items():
            percentage = (cost / report['total_cost_usd'] * 100) if report['total_cost_usd'] > 0 else 0
            print(f"  • {comp:15s}: ${cost:.4f} ({percentage:.1f}%)")
        print(f"{'='*50}\n")


# Global instance (can be passed around or imported)
tracker = CostTracker()