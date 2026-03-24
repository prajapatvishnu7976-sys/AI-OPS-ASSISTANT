"""
✅ VERIFIER AGENT - FIXED VERSION
Proper extraction with detailed logging
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from agents.base_agent import BaseAgent
from utils.logger import logger


class VerifierAgent(BaseAgent):
    """
    ✅ VERIFIER - PROPERLY EXTRACTS ALL DATA
    """
    
    def __init__(self):
        super().__init__(
            agent_id="verifier-001",
            name="Verifier Agent"
        )
        self.confidence_threshold = 0.8
        logger.info(f"✅ {self.name} initialized (FAST MODE)")
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return isinstance(input_data, dict) and "results" in input_data
    
    async def validate_output(self, output_data: Dict[str, Any]) -> bool:
        return isinstance(output_data, dict) and "status" in output_data
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format data"""
        query = input_data.get("query", "")
        results = input_data.get("results", [])
        critique = input_data.get("critique", {})
        
        logger.info(f"✅ Verifier: Processing {len(results)} results")
        
        # Debug: Log each result structure
        for i, r in enumerate(results):
            logger.info(f"   Result[{i}]: tool={r.get('tool')}, status={r.get('status')}")
            result_data = r.get("result")
            if result_data:
                logger.info(f"      Data keys: {list(result_data.keys())}")
                if r.get("tool") == "github":
                    repos = result_data.get("repositories", [])
                    logger.info(f"      Repositories: {len(repos)}")
                elif r.get("tool") == "weather":
                    logger.info(f"      City: {result_data.get('city')}, Temp: {result_data.get('temperature')}")
        
        # Extract data
        weather = self._extract_weather(results)
        repositories = self._extract_repositories(results)
        web_results = self._extract_web_results(results)
        
        logger.info(f"✅ Extracted: Weather={'✅' if weather else '❌'}, Repos={len(repositories) if repositories else 0}")
        
        # Generate summary
        summary = self._generate_summary(weather, repositories, web_results)
        
        successful = sum(1 for r in results if r.get("status") == "completed")
        
        return {
            "status": "success",
            "query": query,
            "summary": summary,
            "weather": weather,
            "repositories": repositories,
            "web_results": web_results,
            "quality": {
                "score": critique.get("quality_score", {}).get("overall", 0.9),
                "grade": critique.get("grade", "A"),
                "issues_count": len(critique.get("issues", []))
            },
            "metadata": {
                "total_steps": len(results),
                "steps_completed": successful,
                "steps_failed": len(results) - successful,
                "timestamp": datetime.now().isoformat()
            },
            "generated_at": datetime.now().isoformat()
        }
    
    async def calculate_confidence(self, input_data: Dict, output: Dict) -> float:
        has_weather = output.get("weather") is not None
        has_repos = output.get("repositories") is not None and len(output.get("repositories", [])) > 0
        
        if has_weather or has_repos:
            return 0.95
        return 0.7
    
    def _extract_weather(self, results: List[Dict]) -> Optional[Dict]:
        """Extract weather data"""
        logger.info("🔍 Extracting weather...")
        
        for result in results:
            tool = result.get("tool")
            status = result.get("status")
            
            if tool == "weather" and status == "completed":
                data = result.get("result")
                
                if not data:
                    logger.warning("   ⚠️ Weather result has no data")
                    continue
                
                if not isinstance(data, dict):
                    logger.warning(f"   ⚠️ Weather data is not dict: {type(data)}")
                    continue
                
                logger.info(f"   ✅ Found weather: {data.get('city')} - {data.get('temperature')}")
                
                return {
                    "city": str(data.get("city", "Unknown")),
                    "country": str(data.get("country", "")),
                    "temperature": str(data.get("temperature", "N/A")),
                    "feels_like": str(data.get("feels_like", "N/A")),
                    "description": str(data.get("description", "")).capitalize(),
                    "humidity": str(data.get("humidity", "N/A")),
                    "wind_speed": str(data.get("wind_speed", "N/A")),
                    "clouds": str(data.get("clouds", "N/A")),
                    "icon": data.get("icon", "01d")
                }
        
        logger.info("   ❌ No weather found")
        return None
    
    def _extract_repositories(self, results: List[Dict]) -> Optional[List[Dict]]:
        """Extract GitHub repositories"""
        logger.info("🔍 Extracting repositories...")
        
        all_repos = []
        
        for result in results:
            tool = result.get("tool")
            status = result.get("status")
            
            if tool == "github" and status == "completed":
                data = result.get("result")
                
                if not data:
                    logger.warning("   ⚠️ GitHub result has no data")
                    continue
                
                if not isinstance(data, dict):
                    logger.warning(f"   ⚠️ GitHub data is not dict: {type(data)}")
                    continue
                
                repos = data.get("repositories", [])
                logger.info(f"   📦 Found {len(repos)} repositories in result")
                
                for repo in repos:
                    formatted = {
                        "name": str(repo.get("name", "Unknown")),
                        "full_name": str(repo.get("full_name", "")),
                        "description": str(repo.get("description", "No description"))[:150],
                        "stars": self._format_number(repo.get("stars", 0)),
                        "stars_raw": int(repo.get("stars", 0)) if repo.get("stars") else 0,
                        "forks": self._format_number(repo.get("forks", 0)),
                        "forks_raw": int(repo.get("forks", 0)) if repo.get("forks") else 0,
                        "language": str(repo.get("language", "Unknown")),
                        "url": str(repo.get("url", "#")),
                        "owner": str(repo.get("owner", "")),
                        "topics": repo.get("topics", [])[:5] if isinstance(repo.get("topics"), list) else []
                    }
                    all_repos.append(formatted)
                    logger.info(f"      ✅ Repo: {formatted['name']} ⭐{formatted['stars']}")
        
        if all_repos:
            logger.info(f"   ✅ Total repositories: {len(all_repos)}")
            return all_repos
        
        logger.info("   ❌ No repositories found")
        return None
    
    def _extract_web_results(self, results: List[Dict]) -> Optional[List[Dict]]:
        """Extract web search results"""
        logger.info("🔍 Extracting web results...")
        
        all_results = []
        
        for result in results:
            if result.get("tool") == "web_search" and result.get("status") == "completed":
                data = result.get("result")
                
                if not data:
                    continue
                
                # AI answer
                answer = data.get("answer", "")
                if answer:
                    all_results.append({
                        "title": "AI Summary",
                        "snippet": str(answer)[:300],
                        "source": "Tavily AI",
                        "is_answer": True
                    })
                
                # Individual results
                for item in data.get("results", []):
                    all_results.append({
                        "title": str(item.get("title", "")),
                        "snippet": str(item.get("snippet", ""))[:200],
                        "url": str(item.get("url", "#")),
                        "source": self._get_domain(item.get("url", ""))
                    })
        
        if all_results:
            logger.info(f"   ✅ Web results: {len(all_results)}")
            return all_results
        
        return None
    
    def _generate_summary(self, weather, repos, web) -> str:
        """Generate summary text"""
        parts = []
        
        if weather:
            parts.append(f"Weather in {weather['city']}: {weather['temperature']}, {weather['description']}")
        
        if repos and len(repos) > 0:
            top = repos[0]
            parts.append(f"Found {len(repos)} repos. Top: {top['name']} ({top['stars']}⭐)")
        
        if web:
            parts.append(f"Found {len(web)} web results")
        
        return " • ".join(parts) if parts else "No results found"
    
    def _format_number(self, num) -> str:
        """Format number (1000 -> 1K)"""
        try:
            n = int(num) if num else 0
            if n >= 1000000:
                return f"{n/1000000:.1f}M"
            elif n >= 1000:
                return f"{n/1000:.1f}K"
            return str(n)
        except:
            return str(num)
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return "Unknown"
        try:
            return url.replace("https://", "").replace("http://", "").split("/")[0].replace("www.", "")
        except:
            return "Unknown"
    
    async def verify_and_format(
        self,
        query: str,
        results: List[Dict],
        critique: Optional[Dict] = None,
        plan: Optional[List[Dict]] = None,
        output_format: str = "standard"
    ) -> Dict:
        """Public API"""
        input_data = {
            "query": query,
            "results": results,
            "critique": critique or {},
            "plan": plan or []
        }
        
        result = await self.execute(input_data)
        
        if result["status"] == "success":
            return result["output"]
        else:
            logger.error(f"❌ Verifier failed: {result.get('error')}")
            return {
                "status": "error",
                "query": query,
                "error": result.get("error", "Unknown")
            }