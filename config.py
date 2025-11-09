import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Centralized configuration for the knowledge extractor."""
    
    # API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = "llama-3.3-70b-versatile"
    TEMPERATURE = 0
    MAX_RETRIES = 3
    
    # Embedding Configuration
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Storage Configuration
    CHROMA_DIR = "chroma_store"
    OUTPUT_FILE = "structured_knowledge.json"
    LOG_FILE = "knowledge_extraction.log"
    
    # Repository Configuration
    REPO_URL = os.getenv("REPO_URL", "")  # Git repository URL
    REPO_PATH = "cloned_code_repo"
    GIT_TOKEN = os.getenv("GIT_TOKEN", "")  # Git Personal Access Token (optional but recommended)
    FILE_EXTENSIONS = [".java"]
    FORCE_CLONE = os.getenv("FORCE_CLONE", "false").lower() == "true"
    
    # Chunking Configuration
    CHUNK_SIZE = 3500  # Conservative to stay under token limits
    CHUNK_OVERLAP = 300
    
    # Processing Configuration
    MAX_CLASSES_IN_OVERVIEW = 20  # Max classes to include in project overview
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GROQ_API_KEY:
            raise ValueError("❌ GROQ_API_KEY not found. Please add it to your .env file.")
        
        if not cls.REPO_URL:
            # Check if repo already exists
            if not os.path.exists(cls.REPO_PATH):
                raise ValueError(
                    "❌ REPO_URL not found in .env and no existing repository at "
                    f"{cls.REPO_PATH}. Please add REPO_URL to your .env file."
                )
    
    @classmethod
    def get_splitter_config(cls):
        """Get text splitter configuration."""
        return {
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "separators": ["\n\nclass ", "\n\npublic ", "\n\nprotected ", 
                          "\n\nprivate ", "\n\n", "\n", " "]
        }