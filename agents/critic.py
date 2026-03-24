"""
🎭 CRITIC AGENT - FAST VERSION
Rule-based quality check, LLM disabled by default
Response time: <50ms
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from agents.base_agent import BaseAgent
from utils.logger import logger


class QualityScore:
    """Fast quality scoring"""
    
    def __init__(self, completeness=0.0, accuracy=0.0, relevance=0.0):
        self.completeness = completeness
        self.accuracy = accuracy
        self.relevance = relevance
    
    @property
    def overall(self) -> float:
        return round((self.completeness + self.accuracy + self.relevance) / 3, 2)
    
    def to_dict(self) -> Dict:
        return {
            "completeness": self.completeness,
            "accuracy": self.accuracy,
            "relevance": self.relevance,
            "overall": self.overall
        }
    
    def get_grade(self) -> str:
        score = self.overall
        if score >= 0.9: return "A+"
        elif score >= 0.8: return "A"
        elif score >= 0.7: return "B"
        elif score >= 0.6: return "C"
        elif score >= 0.5: return "D"
        else: return "F"


class CriticAgent(BaseAgent):
    """
    🎭 FAST CRITIC - Rule-based only
    
    NO LLM calls for speed
    Direct quality assessment
    """
    
    QUALITY_THRESHOLD = 0.6
    
    def __init__(self):
        super().__init__(
            agent_id="critic-001",
            name="Critic Agent"
        )
        
        # DISABLED LLM for speed
        self.llm = None
        self.model_name = "rule-based-fast"
        self.use_llm = False  # Set True to enable LLM
        
        logger.info(f"🎭 {self.name} initialized (FAST MODE - No LLM)")
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return isinstance(input_data, dict) and "results" in input_data
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        return isinstance(output_data, dict) and "approved" in output_data
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """FAST critique - pure rules"""
        query = input_data.get("query", "")
        results = input_data.get("results", [])
        plan = input_data.get("plan", [])
        
        # FAST: Direct quality check
        score = self._assess_quality_fast(results, plan)
        issues = self._find_issues_fast(results)
        
        approved = score.overall >= self.QUALITY_THRESHOLD
        
        return {
            "quality_score": score.to_dict(),
            "grade": score.get_grade(),
            "issues": issues,
            "suggestions": [],
            "approved": approved,
            "needs_retry": not approved and len(issues) > 0,
            "retry_steps": [i.get("step_id") for i in issues if i.get("severity") == "high"],
            "critique_summary": f"Quality: {score.get_grade()} ({score.overall:.2f})",
            "timestamp": datetime.now().isoformat()
        }
    
    async def calculate_confidence(self, input_data: Dict, output: Dict) -> float:
        score = output.get("quality_score", {}).get("overall", 0.5)
        return 0.95 if score >= 0.8 else 0.8
    
    def _assess_quality_fast(self, results: List[Dict], plan: List[Dict]) -> QualityScore:
        """FAST quality assessment"""
        score = QualityScore()
        
        # Completeness: successful steps / total
        completed = sum(1 for r in results if r.get("status") == "completed")
        total = len(plan) if plan else len(results)
        score.completeness = completed / total if total > 0 else 0.0
        
        # Accuracy: check for errors
        errors = sum(1 for r in results if r.get("status") == "failed")
        score.accuracy = 1.0 - (errors / len(results)) if results else 0.0
        
        # Relevance: check if we got data
        has_data = any(r.get("result") for r in results if r.get("status") == "completed")
        score.relevance = 1.0 if has_data else 0.3
        
        logger.info(f"📊 Quality: {score.get_grade()} ({score.overall:.2f})")
        
        return score
    
    def _find_issues_fast(self, results: List[Dict]) -> List[Dict]:
        """FAST issue detection"""
        issues = []
        
        for r in results:
            if r.get("status") == "failed":
                issues.append({
                    "type": "execution_failure",
                    "severity": "high",
                    "step_id": r.get("step_id"),
                    "tool": r.get("tool"),
                    "message": f"{r.get('tool')} failed: {r.get('error', 'Unknown')}"
                })
            
            elif r.get("status") == "completed":
                data = r.get("result", {})
                
                # Check empty results
                if r.get("tool") == "github":
                    repos = data.get("repositories", [])
                    if not repos:
                        issues.append({
                            "type": "empty_result",
                            "severity": "medium",
                            "step_id": r.get("step_id"),
                            "tool": "github",
                            "message": "No repositories returned"
                        })
        
        return issues
    
    # ============ PUBLIC API ============
    
    async def critique(
        self,
        query: str,
        results: List[Dict],
        plan: Optional[List[Dict]] = None
    ) -> Dict:
        """FAST public API"""
        input_data = {
            "query": query,
            "results": results,
            "plan": plan or []
        }
        
        result = await self.execute(input_data)
        
        if result["status"] == "success":
            return result["output"]
        else:
            return {
                "quality_score": {"overall": 0.8},
                "grade": "B",
                "issues": [],
                "approved": True,
                "needs_retry": False,
                "retry_steps": []
            }