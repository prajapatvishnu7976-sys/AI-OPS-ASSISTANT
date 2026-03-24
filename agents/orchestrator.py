"""
🎯 ORCHESTRATOR - FIXED VERSION
Proper data flow between agents
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.critic import CriticAgent
from agents.verifier import VerifierAgent
from utils.logger import logger


class Orchestrator:
    """🎯 ORCHESTRATOR"""
    
    def __init__(self):
        logger.info("🎯 Initializing Fast Orchestrator...")
        
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.critic = CriticAgent()
        self.verifier = VerifierAgent()
        
        self.agents = {
            "planner": self.planner,
            "executor": self.executor,
            "critic": self.critic,
            "verifier": self.verifier
        }
        
        self.current_state = "idle"
        
        logger.info(f"🎯 Orchestrator ready (FAST MODE)")
    
    async def process_query(
        self,
        query: str,
        max_iterations: int = 1,
        enable_critique: bool = True,
        output_format: str = "standard",
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process query through pipeline"""
        start_time = datetime.now()
        
        logger.info(f"\n{'='*50}")
        logger.info(f"🎯 FAST PROCESSING: '{query[:60]}...'")
        logger.info(f"{'='*50}\n")
        
        try:
            # ========== PHASE 1: PLANNING ==========
            self.current_state = "planning"
            logger.info("📋 PHASE 1: Planning...")
            plan_start = datetime.now()
            
            plan = await self.planner.create_plan(query)
            
            plan_time = (datetime.now() - plan_start).total_seconds() * 1000
            logger.info(f"✅ Plan ready: {len(plan)} steps ({plan_time:.0f}ms)")
            
            # ========== PHASE 2: EXECUTION ==========
            self.current_state = "executing"
            logger.info("⚙️ PHASE 2: Executing (parallel)...")
            exec_start = datetime.now()
            
            results = await self.executor.execute_plan(plan)
            
            exec_time = (datetime.now() - exec_start).total_seconds() * 1000
            successful = sum(1 for r in results if r.get("status") == "completed")
            logger.info(f"✅ Executed: {successful}/{len(results)} ({exec_time:.0f}ms)")
            
            # Debug: Log results structure
            logger.info("📋 Results structure:")
            for r in results:
                logger.info(f"   - {r.get('tool')}: status={r.get('status')}, has_result={r.get('result') is not None}")
            
            # ========== PHASE 3: CRITIQUE ==========
            critique_result = {}
            crit_time = 0
            
            if enable_critique:
                self.current_state = "critiquing"
                logger.info("🎭 PHASE 3: Quick critique...")
                crit_start = datetime.now()
                
                critique_result = await self.critic.critique(
                    query=query,
                    results=results,
                    plan=plan
                )
                
                crit_time = (datetime.now() - crit_start).total_seconds() * 1000
                logger.info(f"✅ Quality: {critique_result.get('grade')} ({crit_time:.0f}ms)")
            
            # ========== PHASE 4: FORMAT ==========
            self.current_state = "verifying"
            logger.info("✅ PHASE 4: Formatting...")
            ver_start = datetime.now()
            
            final_output = await self.verifier.verify_and_format(
                query=query,
                results=results,
                critique=critique_result,
                plan=plan
            )
            
            ver_time = (datetime.now() - ver_start).total_seconds() * 1000
            logger.info(f"✅ Formatted ({ver_time:.0f}ms)")
            
            # ========== COMPLETE ==========
            self.current_state = "completed"
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Add timing
            if "metadata" not in final_output:
                final_output["metadata"] = {}
            
            final_output["metadata"]["total_time_ms"] = round(total_time, 2)
            final_output["metadata"]["phase_times"] = {
                "planning_ms": round(plan_time, 2),
                "execution_ms": round(exec_time, 2),
                "critique_ms": round(crit_time, 2),
                "verification_ms": round(ver_time, 2)
            }
            
            # Final log
            weather = final_output.get("weather")
            repos = final_output.get("repositories", [])
            
            logger.info(f"\n{'='*50}")
            logger.info(f"🎯 COMPLETE in {total_time:.0f}ms")
            logger.info(f"   Weather: {'✅ ' + weather.get('city', '') if weather else '❌'}")
            logger.info(f"   Repos: {len(repos) if repos else 0}")
            logger.info(f"   Quality: {final_output.get('quality', {}).get('grade', 'N/A')}")
            logger.info(f"{'='*50}\n")
            
            return final_output
        
        except Exception as e:
            self.current_state = "failed"
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            
            logger.error(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "status": "error",
                "query": query,
                "error": str(e),
                "metadata": {"total_time_ms": round(total_time, 2)}
            }
    
    def get_system_status(self) -> Dict:
        return {
            "orchestrator_state": self.current_state,
            "agents": {name: agent.get_status() for name, agent in self.agents.items()},
            "mode": "FAST"
        }
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict]:
        agent = self.agents.get(agent_name)
        return agent.get_status() if agent else None
    
    def is_healthy(self) -> bool:
        return all(agent.is_healthy() for agent in self.agents.values())
    
    async def shutdown(self):
        logger.info("🎯 Shutting down...")
        await self.executor.close()
        logger.info("✅ Done")


_orchestrator_instance: Optional[Orchestrator] = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = Orchestrator()
    return _orchestrator_instance

async def process_query(query: str, **kwargs) -> Dict:
    return await get_orchestrator().process_query(query, **kwargs)