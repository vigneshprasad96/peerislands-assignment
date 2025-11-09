import json
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Config
from logger import logger


class LLMService:
    """Service class for LLM interactions."""
    
    def __init__(self):
        """Initialize LLM service with Groq client."""
        self.llm = ChatGroq(
            api_key=Config.GROQ_API_KEY,
            model=Config.GROQ_MODEL,
            temperature=Config.TEMPERATURE
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            **Config.get_splitter_config()
        )
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text safely to stay under token limits.
        
        Args:
            text: Text to chunk
        
        Returns:
            List of text chunks
        """
        return self.text_splitter.split_text(text)
    
    def call_with_retry(self, messages: List, max_retries: int = Config.MAX_RETRIES) -> Optional[str]:
        """
        Call LLM with retry logic for resilience.
        
        Args:
            messages: List of messages to send
            max_retries: Maximum number of retry attempts
        
        Returns:
            LLM response or None if all attempts fail
        """
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} attempts failed")
                    return None
        return None
    
    def extract_class_summary(self, class_info: Dict[str, Any]) -> str:
        """
        Extract a detailed summary for a single class.
        
        Args:
            class_info: Dictionary containing class information
        
        Returns:
            LLM-generated summary
        """
        class_json = json.dumps({
            "name": class_info["name"],
            "type": class_info.get("type", "class"),
            "extends": class_info.get("extends"),
            "implements": class_info.get("implements"),
            "methods": [
                {"signature": m["signature"], "complexity": m["complexity"]} 
                for m in class_info.get("methods", [])
            ],
            "fields": class_info.get("fields", [])
        }, indent=2)
        
        prompt = f"""Analyze this Java class and provide a structured summary:

{class_json}

Please provide:
1. Purpose: What is the main purpose of this class?
2. Responsibilities: What are its key responsibilities?
3. Key Methods: Describe the most important methods (max 3-5)
4. Complexity Assessment: Comment on the overall complexity
5. Design Patterns: Identify any design patterns used

Keep the response concise and structured."""

        messages = [
            SystemMessage(content="You are a senior software architect analyzing Java code. Provide clear, structured summaries."),
            HumanMessage(content=prompt)
        ]
        
        return self.call_with_retry(messages) or "Summary unavailable"
    
    def extract_project_overview(self, all_classes: List[Dict[str, Any]], packages: List[str]) -> str:
        """
        Generate high-level project overview.
        
        Args:
            all_classes: List of all parsed classes
            packages: List of package names
        
        Returns:
            LLM-generated project overview
        """
        stats = {
            "total_classes": len(all_classes),
            "total_methods": sum(c.get("method_count", 0) for c in all_classes),
            "packages": list(set(packages)),
            "avg_complexity": sum(c.get("avg_complexity", 0) for c in all_classes) / len(all_classes) if all_classes else 0
        }
        
        class_names = ', '.join([c['name'] for c in all_classes[:Config.MAX_CLASSES_IN_OVERVIEW]])
        if len(all_classes) > Config.MAX_CLASSES_IN_OVERVIEW:
            class_names += '...'
        
        prompt = f"""Analyze this Java project based on the following statistics:

{json.dumps(stats, indent=2)}

Class names: {class_names}

Provide a high-level overview including:
1. Project Purpose: What does this application do?
2. Architecture: What architectural patterns are used?
3. Main Components: What are the primary modules/components?
4. Technology Stack: What frameworks/libraries are evident?
5. Code Quality: Assessment based on complexity metrics

Keep it concise (200-300 words)."""

        messages = [
            SystemMessage(content="You are a senior software architect reviewing a codebase. Provide insightful analysis."),
            HumanMessage(content=prompt)
        ]
        
        return self.call_with_retry(messages) or "Overview unavailable"