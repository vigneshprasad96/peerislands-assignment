from typing import Dict, Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import Config
from logger import logger


class VectorStoreManager:
    """Manages vector storage for semantic search."""
    
    def __init__(self):
        """Initialize vector store with embeddings."""
        logger.info("Initializing vector store...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=Config.EMBEDDING_MODEL
        )
        self.vector_store = Chroma(
            persist_directory=Config.CHROMA_DIR,
            embedding_function=self.embeddings
        )
    
    def store_knowledge(self, structured_knowledge: Dict[str, Any]) -> None:
        """
        Store knowledge in vector database for semantic search.
        
        Args:
            structured_knowledge: Structured knowledge dictionary
        """
        logger.info("Storing knowledge in vector database...")
        
        # Store project overview
        self._store_project_overview(structured_knowledge.get("project_overview", ""))
        
        # Store class summaries
        self._store_classes(structured_knowledge.get("classes", []))
        
        # Store interface information
        self._store_interfaces(structured_knowledge.get("interfaces", []))
        
        logger.info("Vector database updated successfully")
    
    def _store_project_overview(self, overview: str) -> None:
        """
        Store project overview in vector DB.
        
        Args:
            overview: Project overview text
        """
        if not overview:
            return
        
        self.vector_store.add_texts(
            texts=[overview],
            metadatas=[{"type": "project_overview"}]
        )
    
    def _store_classes(self, classes: list) -> None:
        """
        Store class information in vector DB.
        
        Args:
            classes: List of class dictionaries
        """
        for cls in classes:
            text = self._format_class_text(cls)
            self.vector_store.add_texts(
                texts=[text],
                metadatas=[{
                    "type": "class",
                    "class_name": cls["name"],
                    "package": cls.get("package", "N/A")
                }]
            )
    
    def _store_interfaces(self, interfaces: list) -> None:
        """
        Store interface information in vector DB.
        
        Args:
            interfaces: List of interface dictionaries
        """
        for interface in interfaces:
            text = self._format_interface_text(interface)
            self.vector_store.add_texts(
                texts=[text],
                metadatas=[{
                    "type": "interface",
                    "interface_name": interface["name"]
                }]
            )
    
    def _format_class_text(self, cls: Dict[str, Any]) -> str:
        """
        Format class information for vector storage.
        
        Args:
            cls: Class dictionary
        
        Returns:
            Formatted text
        """
        text_parts = [
            f"Class: {cls['name']}",
            f"Package: {cls.get('package', 'N/A')}",
            f"Methods: {cls.get('method_count', 0)}",
            f"Summary: {cls.get('summary', 'No summary available')}"
        ]
        
        if cls.get('extends'):
            text_parts.append(f"Extends: {cls['extends']}")
        
        if cls.get('implements'):
            text_parts.append(f"Implements: {', '.join(cls['implements'])}")
        
        return "\n".join(text_parts)
    
    def _format_interface_text(self, interface: Dict[str, Any]) -> str:
        """
        Format interface information for vector storage.
        
        Args:
            interface: Interface dictionary
        
        Returns:
            Formatted text
        """
        text_parts = [
            f"Interface: {interface['name']}",
            f"Methods: {interface.get('method_count', 0)}"
        ]
        
        if interface.get('extends'):
            text_parts.append(f"Extends: {', '.join(interface['extends'])}")
        
        return "\n".join(text_parts)
    
    def search(self, query: str, k: int = 5) -> list:
        """
        Search vector store for relevant information.
        
        Args:
            query: Search query
            k: Number of results to return
        
        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        results = self.vector_store.similarity_search(query, k=k)
        return results