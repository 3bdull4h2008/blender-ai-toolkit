"""Base API classes for AI Toolkit"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class GenerationRequest:
    """Base class for all generation requests."""
    prompt: str
    model_id: str = ""
    provider_id: str = ""
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}

@dataclass
class GenerationResult:
    """Result of a generation operation."""
    success: bool
    text_response: str = ""
    output_files: List[str] = None
    error: str = ""
    
    def __post_init__(self):
        if self.output_files is None:
            self.output_files = []
