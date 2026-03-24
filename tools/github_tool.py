"""
📦 GITHUB TOOL
Fetches repositories from GitHub API
FREE - No API key required for basic search
"""

import aiohttp
from typing import Dict, Any, List, Optional
from utils.logger import logger


class GitHubTool:
    """
    📦 GitHub Repository Search Tool
    
    Uses GitHub's public API (no auth required for basic search)
    Rate limit: 10 requests/minute (unauthenticated)
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-Operations-Assistant"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_repos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search GitHub repositories
        
        Args:
            params: {
                "query": "python",
                "limit": 5,
                "language": "python" (optional)
            }
        
        Returns:
            {
                "repositories": [...],
                "total_count": 100,
                "query": "python"
            }
        """
        query = params.get("query", "trending")
        limit = min(params.get("limit", 5), 10)
        language = params.get("language", "")
        
        # Build search query
        search_query = query
        if language:
            search_query += f" language:{language}"
        
        logger.info(f"📦 GitHub: Searching '{search_query}' (limit: {limit})")
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=15)
                )
            
            url = f"{self.BASE_URL}/search/repositories"
            params_api = {
                "q": search_query,
                "sort": "stars",
                "order": "desc",
                "per_page": limit
            }
            
            async with self.session.get(url, params=params_api, headers=self.headers) as response:
                if response.status == 403:
                    logger.warning("⚠️ GitHub rate limit reached")
                    return {
                        "repositories": [],
                        "error": "Rate limit exceeded",
                        "query": query
                    }
                
                if response.status != 200:
                    logger.error(f"❌ GitHub API error: {response.status}")
                    return {
                        "repositories": [],
                        "error": f"API error: {response.status}",
                        "query": query
                    }
                
                data = await response.json()
                
                repositories = []
                for item in data.get("items", [])[:limit]:
                    repo = {
                        "name": item.get("name", ""),
                        "full_name": item.get("full_name", ""),
                        "description": item.get("description") or "No description",
                        "stars": item.get("stargazers_count", 0),
                        "forks": item.get("forks_count", 0),
                        "language": item.get("language") or "Unknown",
                        "url": item.get("html_url", ""),
                        "owner": item.get("owner", {}).get("login", ""),
                        "topics": item.get("topics", [])[:5],
                        "updated_at": item.get("updated_at", ""),
                        "open_issues": item.get("open_issues_count", 0)
                    }
                    repositories.append(repo)
                
                logger.info(f"✅ GitHub: Found {len(repositories)} repos")
                
                return {
                    "repositories": repositories,
                    "total_count": data.get("total_count", 0),
                    "query": query
                }
        
        except aiohttp.ClientError as e:
            logger.error(f"❌ GitHub connection error: {e}")
            return {
                "repositories": [],
                "error": str(e),
                "query": query
            }
        except Exception as e:
            logger.error(f"❌ GitHub error: {e}")
            return {
                "repositories": [],
                "error": str(e),
                "query": query
            }
    
    async def get_trending(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get trending repositories"""
        # Use search with stars:>1000
        params["query"] = f"{params.get('query', '')} stars:>1000"
        return await self.search_repos(params)


# Singleton instance
_github_tool: Optional[GitHubTool] = None

async def get_github_tool() -> GitHubTool:
    global _github_tool
    if _github_tool is None:
        _github_tool = GitHubTool()
        await _github_tool.__aenter__()
    return _github_tool