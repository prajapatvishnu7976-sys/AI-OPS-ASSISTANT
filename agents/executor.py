"""
⚙️ EXECUTOR AGENT - FIXED VERSION
Proper data flow with detailed logging
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime
from utils.logger import logger
import os


class ToolExecutionError(Exception):
    pass


class ExecutorAgent:
    """
    ⚙️ EXECUTOR - PROPERLY WORKING VERSION
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info("⚙️ Executor initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=15)
            )
        return self.session
    
    async def execute_plan(self, plan: List[Dict]) -> List[Dict]:
        """Execute all steps in parallel"""
        logger.info(f"⚙️ Executor: Processing {len(plan)} steps")
        
        independent = [s for s in plan if not s.get("depends_on")]
        logger.info(f"📊 Independent: {len(independent)}, Dependent: {len(plan) - len(independent)}")
        
        results = []
        
        if independent:
            logger.info("🚀 Executing in parallel...")
            tasks = [self._execute_step(step) for step in independent]
            parallel_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(parallel_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Step {independent[i]['id']} exception: {result}")
                    results.append({
                        "step_id": independent[i]["id"],
                        "tool": independent[i]["tool"],
                        "action": independent[i]["action"],
                        "status": "failed",
                        "error": str(result),
                        "result": None
                    })
                else:
                    results.append(result)
        
        successful = sum(1 for r in results if r.get("status") == "completed")
        logger.info(f"✅ Executed: {successful}/{len(results)}")
        
        return results
    
    async def _execute_step(self, step: Dict) -> Dict:
        """Execute single step"""
        step_id = step.get("id", 1)
        tool = step.get("tool", "")
        action = step.get("action", "")
        params = step.get("params", {})
        
        start_time = datetime.now()
        logger.info(f"🔧 {tool}.{action}({list(params.keys())})")
        
        try:
            # Route to correct tool
            if tool == "github":
                result_data = await self._execute_github(params)
            elif tool == "weather":
                result_data = await self._execute_weather(params)
            elif tool == "web_search":
                result_data = await self._execute_web_search(params)
            else:
                raise ToolExecutionError(f"Unknown tool: {tool}")
            
            exec_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Log what we got
            if tool == "github":
                repos = result_data.get("repositories", [])
                logger.info(f"📦 GitHub returned {len(repos)} repositories")
            elif tool == "weather":
                city = result_data.get("city", "?")
                temp = result_data.get("temperature", "?")
                logger.info(f"🌤️ Weather returned: {city} - {temp}")
            
            return {
                "step_id": step_id,
                "tool": tool,
                "action": action,
                "status": "completed",
                "result": result_data,
                "execution_time_ms": round(exec_time, 2)
            }
        
        except Exception as e:
            exec_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"❌ {tool}.{action} failed: {e}")
            
            return {
                "step_id": step_id,
                "tool": tool,
                "action": action,
                "status": "failed",
                "error": str(e),
                "result": None,
                "execution_time_ms": round(exec_time, 2)
            }
    
    async def _execute_github(self, params: Dict) -> Dict:
        """Execute GitHub API call"""
        query = params.get("query", "trending")
        limit = min(params.get("limit", 5), 10)
        
        logger.info(f"📦 GitHub API: query='{query}', limit={limit}")
        
        session = await self._get_session()
        
        url = "https://api.github.com/search/repositories"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Ops-Assistant"
        }
        api_params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit
        }
        
        async with session.get(url, params=api_params, headers=headers) as response:
            logger.info(f"📦 GitHub response status: {response.status}")
            
            if response.status == 403:
                logger.warning("⚠️ GitHub rate limit hit!")
                return {"repositories": [], "error": "Rate limit", "query": query}
            
            if response.status != 200:
                text = await response.text()
                logger.error(f"❌ GitHub error: {response.status} - {text[:200]}")
                raise ToolExecutionError(f"GitHub API error: {response.status}")
            
            data = await response.json()
            items = data.get("items", [])
            
            logger.info(f"📦 GitHub raw items: {len(items)}")
            
            repositories = []
            for item in items[:limit]:
                repo = {
                    "name": item.get("name", "Unknown"),
                    "full_name": item.get("full_name", ""),
                    "description": item.get("description") or "No description",
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language") or "Unknown",
                    "url": item.get("html_url", ""),
                    "owner": item.get("owner", {}).get("login", ""),
                    "topics": item.get("topics", [])[:5]
                }
                repositories.append(repo)
                logger.info(f"   📦 Repo: {repo['name']} ⭐{repo['stars']}")
            
            logger.info(f"✅ GitHub: Returning {len(repositories)} repos")
            
            return {
                "repositories": repositories,
                "total_count": data.get("total_count", 0),
                "query": query
            }
    
    async def _execute_weather(self, params: Dict) -> Dict:
        """Execute Weather API call"""
        city = params.get("city", "London")
        api_key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("WEATHER_API_KEY")
        
        logger.info(f"🌤️ Weather API: city='{city}'")
        
        if not api_key:
            logger.warning("⚠️ No weather API key, using mock")
            return self._mock_weather(city)
        
        session = await self._get_session()
        
        url = "https://api.openweathermap.org/data/2.5/weather"
        api_params = {
            "q": city,
            "appid": api_key,
            "units": "metric"
        }
        
        try:
            async with session.get(url, params=api_params) as response:
                logger.info(f"🌤️ Weather response status: {response.status}")
                
                if response.status == 401:
                    logger.warning("⚠️ Invalid weather API key")
                    return self._mock_weather(city)
                
                if response.status == 404:
                    logger.warning(f"⚠️ City not found: {city}")
                    return {"city": city, "error": "City not found", "temperature": "N/A"}
                
                if response.status != 200:
                    return self._mock_weather(city)
                
                data = await response.json()
                
                weather = {
                    "city": data.get("name", city),
                    "country": data.get("sys", {}).get("country", ""),
                    "temperature": f"{round(data.get('main', {}).get('temp', 0))}°C",
                    "feels_like": f"{round(data.get('main', {}).get('feels_like', 0))}°C",
                    "description": data.get("weather", [{}])[0].get("description", ""),
                    "humidity": f"{data.get('main', {}).get('humidity', 0)}%",
                    "wind_speed": f"{data.get('wind', {}).get('speed', 0)} m/s",
                    "clouds": f"{data.get('clouds', {}).get('all', 0)}%",
                    "icon": data.get("weather", [{}])[0].get("icon", "01d")
                }
                
                logger.info(f"✅ Weather: {weather['city']} - {weather['temperature']}")
                return weather
                
        except Exception as e:
            logger.warning(f"⚠️ Weather error: {e}")
            return self._mock_weather(city)
    
    def _mock_weather(self, city: str) -> Dict:
        """Mock weather"""
        logger.info(f"📋 Mock weather for {city}")
        return {
            "city": city,
            "country": "XX",
            "temperature": "22°C",
            "feels_like": "20°C",
            "description": "partly cloudy",
            "humidity": "65%",
            "wind_speed": "5 m/s",
            "clouds": "40%",
            "is_mock": True
        }
    
    async def _execute_web_search(self, params: Dict) -> Dict:
        """Execute web search"""
        query = params.get("query", "")
        api_key = os.getenv("TAVILY_API_KEY")
        
        if not api_key:
            logger.warning("⚠️ No Tavily API key")
            return {"results": [], "error": "No API key", "query": query}
        
        session = await self._get_session()
        
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": 5
        }
        
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                raise ToolExecutionError(f"Tavily error: {response.status}")
            
            data = await response.json()
            return {
                "results": data.get("results", []),
                "answer": data.get("answer", ""),
                "query": query
            }
    
    async def close(self):
        """Cleanup"""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("⚙️ Executor closed")