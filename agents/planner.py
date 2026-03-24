"""
🧠 PLANNER AGENT
Converts natural language queries to structured execution plans.
FIXED: Multi-query detection, City extraction, Better parsing
"""

import json
import re
import asyncio
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from agents.base_agent import BaseAgent, AgentStatus, MessageType
from utils.logger import logger
from utils.cost_tracker import CostTracker
import os


class PlannerAgent(BaseAgent):
    """
    🧠 PLANNER AGENT
    
    Responsibilities:
    - Parse natural language queries
    - Generate structured JSON execution plans
    - Detect MULTIPLE queries in single input
    - Learn from past planning successes/failures
    """
    
    AVAILABLE_TOOLS = {
        "weather": {
            "description": "Get current weather for a city",
            "actions": ["get_weather"],
            "params": {"city": "string"},
            "examples": ["weather in Tokyo", "Paris temperature", "London forecast"]
        },
        "github": {
            "description": "Search GitHub repositories",
            "actions": ["search_repos", "get_trending", "get_repo_details"],
            "params": {"query": "string", "limit": "number", "language": "string"},
            "examples": ["top Python repos", "trending Rust projects", "5 JavaScript libraries"]
        },
        "web_search": {
            "description": "General web search using Tavily",
            "actions": ["search", "news_search"],
            "params": {"query": "string", "max_results": "number"},
            "examples": ["latest AI news", "how to learn Python", "best practices React"]
        }
    }
    
    # Common cities list for better detection
    KNOWN_CITIES = [
        "tokyo", "paris", "london", "new york", "los angeles", "chicago", 
        "seattle", "san francisco", "boston", "miami", "delhi", "mumbai",
        "bangalore", "hyderabad", "chennai", "kolkata", "pune", "jaipur",
        "beijing", "shanghai", "hong kong", "singapore", "sydney", "melbourne",
        "toronto", "vancouver", "berlin", "frankfurt", "amsterdam", "rome",
        "milan", "madrid", "barcelona", "dubai", "moscow", "seoul", "osaka"
    ]
    
    def __init__(self, model_name: str = "gemini-2.0-flash"):
        super().__init__(
            agent_id="planner-001",
            name="Planner Agent"
        )
        
        # Initialize LLM
        gemini_key = os.getenv("GOOGLE_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if gemini_key:
            logger.info("🧠 Planner using Gemini 2.0 Flash (FREE)")
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                google_api_key=gemini_key,
                temperature=0.1,
                max_retries=3
            )
            self.model_name = "gemini-2.0-flash"
        elif openai_key:
            logger.info("🧠 Planner using OpenAI GPT-3.5")
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                api_key=openai_key
            )
            self.model_name = "gpt-3.5-turbo"
        else:
            raise ValueError("No API key found! Set GOOGLE_API_KEY or OPENAI_API_KEY")
        
        self.cost_tracker = CostTracker()
        self.confidence_threshold = 0.75
        
        # Planning-specific memory
        self.successful_patterns: List[Dict] = []
        self.failed_patterns: List[Dict] = []
        
        logger.info(f"🧠 {self.name} initialized with {self.model_name}")
    
    # ============ ABSTRACT METHOD IMPLEMENTATIONS ============
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate planning request"""
        if not isinstance(input_data, dict):
            return False
        
        query = input_data.get("query", "")
        if not query or not isinstance(query, str):
            logger.error("❌ Planner: Missing or invalid 'query' in input")
            return False
        
        if len(query.strip()) < 3:
            logger.error("❌ Planner: Query too short")
            return False
        
        return True
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate generated plan"""
        if not isinstance(output_data, dict):
            return False
        
        plan = output_data.get("plan", [])
        if not isinstance(plan, list):
            return False
        
        for step in plan:
            if not isinstance(step, dict):
                return False
            if "tool" not in step or "action" not in step:
                return False
        
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main planning logic"""
        query = input_data["query"]
        context = input_data.get("context", [])
        
        logger.info(f"🧠 Planning for: '{query}'")
        
        # Check memory for similar patterns
        relevant_memories = self.memory.recall(query, limit=3)
        
        # Try LLM-based planning first
        try:
            plan = await self._generate_llm_plan(query, context, relevant_memories)
            method = "llm"
        except Exception as e:
            logger.warning(f"⚠️ LLM planning failed: {e}")
            plan = self._generate_fallback_plan(query)
            method = "fallback"
        
        # Optimize plan
        optimized_plan = self._optimize_plan(plan)
        
        return {
            "plan": optimized_plan,
            "method": method,
            "query": query,
            "tool_count": len(optimized_plan),
            "parallel_possible": self._can_parallelize(optimized_plan)
        }
    
    async def calculate_confidence(self, input_data: Dict, output: Dict) -> float:
        """Calculate plan confidence"""
        confidence = 0.0
        
        plan = output.get("plan", [])
        method = output.get("method", "unknown")
        
        if method == "llm":
            confidence += 0.4
        elif method == "fallback":
            confidence += 0.3
        
        valid_steps = sum(1 for s in plan if s.get("tool") in self.AVAILABLE_TOOLS)
        if plan:
            confidence += (valid_steps / len(plan)) * 0.3
        
        params_filled = sum(1 for s in plan if s.get("params") and len(s["params"]) > 0)
        if plan:
            confidence += (params_filled / len(plan)) * 0.2
        
        query = input_data.get("query", "").lower()
        for pattern in self.successful_patterns[-10:]:
            if any(word in query for word in pattern.get("keywords", [])):
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    async def self_improve(self, input_data: Dict, current_output: Dict, confidence: float) -> Dict:
        """Try to improve low-confidence plan"""
        logger.info(f"🔄 Planner self-improving (confidence: {confidence:.2f})")
        
        query = input_data["query"]
        current_plan = current_output.get("plan", [])
        
        if current_output.get("method") == "llm" and confidence < 0.5:
            fallback_plan = self._generate_fallback_plan(query)
            return {
                **current_output,
                "plan": fallback_plan,
                "method": "fallback_improved"
            }
        
        improved_plan = []
        for step in current_plan:
            if not step.get("params"):
                step["params"] = self._infer_params(query, step["tool"])
            improved_plan.append(step)
        
        return {
            **current_output,
            "plan": improved_plan,
            "method": f"{current_output.get('method')}_improved"
        }
    
    # ============ PLANNING METHODS ============
    
    async def _generate_llm_plan(self, query: str, context: List[Dict], memories: List[Dict]) -> List[Dict]:
        """Generate plan using LLM"""
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, context, memories)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm.ainvoke(messages)
        content = response.content
        
        logger.debug(f"📝 LLM Response: {content[:300]}...")
        
        self.cost_tracker.add_llm_cost(
            component="planner",
            model=self.model_name,
            prompt=system_prompt + user_prompt,
            completion=content,
            operation="plan_generation"
        )
        
        plan_data = self._extract_json(content)
        return self._validate_steps(plan_data.get("steps", []))
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        tools_desc = json.dumps(self.AVAILABLE_TOOLS, indent=2)
        
        return f"""You are a Planning Agent. Convert queries to JSON plans.

TOOLS:
{tools_desc}

OUTPUT FORMAT:
{{"steps": [{{"id": 1, "tool": "weather", "action": "get_weather", "params": {{"city": "Tokyo"}}, "depends_on": [], "priority": 1}}]}}

RULES:
1. ONLY output JSON
2. Create separate steps for each task
3. Weather and GitHub can run in parallel (depends_on: [])

EXAMPLES:
Query: "weather in Tokyo and top 5 Python repos"
{{"steps": [{{"id": 1, "tool": "weather", "action": "get_weather", "params": {{"city": "Tokyo"}}, "depends_on": [], "priority": 1}}, {{"id": 2, "tool": "github", "action": "search_repos", "params": {{"query": "python", "limit": 5}}, "depends_on": [], "priority": 1}}]}}"""

    def _build_user_prompt(self, query: str, context: List, memories: List) -> str:
        """Build user prompt"""
        return f'Query: "{query}"\nGenerate JSON plan:'
    
    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        text = text.strip()
        
        if "```json" in text:
            match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
        elif "```" in text:
            match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
        
        start = text.find('{')
        end = text.rfind('}')
        
        if start == -1 or end == -1:
            raise ValueError("No JSON found")
        
        json_str = text[start:end+1]
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def _validate_steps(self, steps: List[Dict]) -> List[Dict]:
        """Validate and normalize steps"""
        validated = []
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            
            validated_step = {
                "id": step.get("id", i + 1),
                "tool": step.get("tool", "web_search"),
                "action": step.get("action", "search"),
                "params": step.get("params", {}),
                "depends_on": step.get("depends_on", []),
                "priority": step.get("priority", 5),
                "status": "pending",
                "result": None,
                "error": None,
                "execution_time_ms": None
            }
            validated.append(validated_step)
        
        return validated
    
    def _generate_fallback_plan(self, query: str) -> List[Dict]:
        """
        🎯 SMART FALLBACK - Properly detects multiple queries
        FIXED: City extraction, conjunction handling
        """
        query_lower = query.lower().strip()
        steps = []
        step_id = 1
        
        logger.info(f"📋 Parsing query: '{query_lower}'")
        
        # ========== SPLIT BY "AND" FIRST ==========
        # Split query into parts by "and", "&", ","
        parts = re.split(r'\s+and\s+|\s*&\s*|\s*,\s*', query_lower)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # Check if this part is about weather
            weather_keywords = ["weather", "temperature", "forecast", "climate", "humid", "rain", "sunny", "cold", "hot", "warm"]
            has_weather = any(kw in part for kw in weather_keywords)
            
            # Check if this part is about GitHub
            github_keywords = ["github", "repo", "repos", "repository", "repositories", "code", "project", "projects", "library", "libraries", "framework", "trending", "top", "best", "popular"]
            has_github = any(kw in part for kw in github_keywords)
            
            # Check if it mentions a programming language (for GitHub)
            programming_languages = [
                "python", "javascript", "typescript", "rust", "go", "golang", 
                "java", "cpp", "c++", "ruby", "php", "swift", "kotlin",
                "react", "vue", "angular", "node", "nodejs", "django", "flask",
                "fastapi", "tensorflow", "pytorch", "machine learning", "ai"
            ]
            has_programming = any(lang in part for lang in programming_languages)
            
            if has_weather:
                # Extract city from this part
                city = self._extract_city_from_part(part)
                if city:
                    steps.append({
                        "id": step_id,
                        "tool": "weather",
                        "action": "get_weather",
                        "params": {"city": city},
                        "depends_on": [],
                        "priority": 1,
                        "status": "pending",
                        "result": None,
                        "error": None,
                        "execution_time_ms": None
                    })
                    step_id += 1
                    logger.info(f"   ✅ Added weather step for: {city}")
            
            elif has_github or has_programming:
                # Extract GitHub search params
                search_query, limit = self._extract_github_params_from_part(part)
                steps.append({
                    "id": step_id,
                    "tool": "github",
                    "action": "search_repos",
                    "params": {"query": search_query, "limit": limit},
                    "depends_on": [],
                    "priority": 2,
                    "status": "pending",
                    "result": None,
                    "error": None,
                    "execution_time_ms": None
                })
                step_id += 1
                logger.info(f"   ✅ Added GitHub step for: {search_query} (limit: {limit})")
            
            else:
                # Check if part has a number with language (like "5 python repos")
                num_lang_match = re.search(r'(\d+)\s*(python|javascript|rust|go|java|react|vue|node)', part)
                if num_lang_match:
                    limit = int(num_lang_match.group(1))
                    lang = num_lang_match.group(2)
                    steps.append({
                        "id": step_id,
                        "tool": "github",
                        "action": "search_repos",
                        "params": {"query": lang, "limit": min(limit, 10)},
                        "depends_on": [],
                        "priority": 2,
                        "status": "pending",
                        "result": None,
                        "error": None,
                        "execution_time_ms": None
                    })
                    step_id += 1
                    logger.info(f"   ✅ Added GitHub step for: {lang} (limit: {limit})")
        
        # ========== FALLBACK: If no steps created, do web search ==========
        if not steps:
            steps.append({
                "id": 1,
                "tool": "web_search",
                "action": "search",
                "params": {"query": query, "max_results": 5},
                "depends_on": [],
                "priority": 5,
                "status": "pending",
                "result": None,
                "error": None,
                "execution_time_ms": None
            })
            logger.info(f"   ✅ Added web search fallback")
        
        logger.info(f"📋 Fallback generated {len(steps)} step(s)")
        return steps
    
    def _extract_city_from_part(self, part: str) -> Optional[str]:
        """
        Extract SINGLE city from a query part
        FIXED: Stops at conjunctions, handles edge cases
        """
        part = part.lower().strip()
        
        # Method 1: Check against known cities
        for city in self.KNOWN_CITIES:
            if city in part:
                return city.title()
        
        # Method 2: Pattern "in/at/for CITY"
        # Match only single word after preposition, stop at conjunctions
        patterns = [
            r'\b(?:in|at|for)\s+([a-zA-Z]+)\b',  # Single word only
            r'\b([a-zA-Z]+)\s+weather\b',  # "Tokyo weather"
            r'\bweather\s+(?:in|at|for)?\s*([a-zA-Z]+)\b',  # "weather in Tokyo"
        ]
        
        skip_words = [
            "the", "a", "an", "and", "or", "top", "best", "get", "show", "find", 
            "what", "check", "current", "today", "now", "please", "me", "tell",
            "weather", "temperature", "forecast", "repos", "repositories"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, part, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                if city.lower() not in skip_words and len(city) > 2:
                    return city.title()
        
        # Method 3: Find any capitalized word that could be a city
        words = part.split()
        for word in words:
            clean = re.sub(r'[^a-zA-Z]', '', word)
            if clean and clean.lower() not in skip_words and len(clean) > 2:
                # Check if it looks like a proper noun
                if clean[0].isupper() or clean.lower() in self.KNOWN_CITIES:
                    return clean.title()
        
        return None
    
    def _extract_github_params_from_part(self, part: str) -> tuple:
        """Extract GitHub search parameters from a query part"""
        
        # Programming languages
        languages = [
            "python", "javascript", "typescript", "rust", "go", "golang", 
            "java", "cpp", "c++", "ruby", "php", "swift", "kotlin",
            "react", "vue", "angular", "node", "nodejs", "django", "flask",
            "fastapi", "tensorflow", "pytorch"
        ]
        
        # Default values
        search_query = "trending"
        limit = 5
        
        # Extract number
        num_match = re.search(r'\b(\d+)\b', part)
        if num_match:
            limit = min(int(num_match.group(1)), 10)
        
        # Extract language
        for lang in languages:
            if lang in part.lower():
                search_query = lang
                break
        
        return search_query, limit
    
    def _infer_params(self, query: str, tool: str) -> Dict:
        """Infer missing params"""
        if tool == "weather":
            city = self._extract_city_from_part(query)
            return {"city": city or "London"}
        elif tool == "github":
            q, limit = self._extract_github_params_from_part(query)
            return {"query": q, "limit": limit}
        else:
            return {"query": query, "max_results": 5}
    
    def _optimize_plan(self, plan: List[Dict]) -> List[Dict]:
        """Optimize plan for parallel execution"""
        independent_steps = [s for s in plan if not s.get("depends_on")]
        for step in independent_steps:
            step["priority"] = 1
        return plan
    
    def _can_parallelize(self, plan: List[Dict]) -> bool:
        """Check if plan has parallel steps"""
        independent = [s for s in plan if not s.get("depends_on")]
        return len(independent) > 1
    
    # ============ PUBLIC API ============
    
    async def create_plan(self, query: str, memory_context: Optional[List[Dict]] = None) -> List[Dict]:
        """Public API - Create execution plan"""
        input_data = {
            "query": query,
            "context": memory_context or []
        }
        
        result = await self.execute(input_data)
        
        if result["status"] == "success":
            return result["output"]["plan"]
        else:
            logger.error(f"❌ Planning failed: {result['error']}")
            return self._generate_fallback_plan(query)
    
    async def refine_plan(self, current_plan: List[Dict], feedback: str) -> List[Dict]:
        """Refine existing plan based on feedback"""
        logger.info(f"🔄 Refining plan based on feedback: {feedback[:100]}")
        
        self.memory.remember({
            "type": "feedback",
            "plan_summary": str(current_plan)[:200],
            "feedback": feedback
        })
        
        return current_plan