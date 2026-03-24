from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """Base class for all tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool action."""
        pass
    
    def validate_params(self, required: list, provided: Dict) -> bool:
        """Validate required parameters."""
        missing = [p for p in required if p not in provided]
        if missing:
            raise ValueError(f"Missing parameters: {missing}")
        return True