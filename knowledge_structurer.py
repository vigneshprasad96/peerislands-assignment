from typing import List, Dict, Any
from datetime import datetime
from logger import logger
from llm_service import LLMService


class KnowledgeStructurer:
    """Structures and organizes extracted knowledge."""
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize knowledge structurer.
        
        Args:
            llm_service: LLM service instance
        """
        self.llm_service = llm_service
    
    def structure_knowledge(self, parsed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Structure extracted knowledge into comprehensive JSON.
        
        Args:
            parsed_files: List of parsed file data
        
        Returns:
            Structured knowledge dictionary
        """
        logger.info("Structuring knowledge...")
        
        # Aggregate all classes and interfaces
        all_classes = []
        all_interfaces = []
        packages = []
        
        for file_data in parsed_files:
            all_classes.extend(file_data["classes"])
            all_interfaces.extend(file_data["interfaces"])
            if file_data["package"]:
                packages.append(file_data["package"])
        
        logger.info(f"Processing {len(all_classes)} classes and {len(all_interfaces)} interfaces")
        
        # Generate project overview
        logger.info("Generating project overview...")
        project_overview = self.llm_service.extract_project_overview(all_classes, packages)
        
        # Process each class
        class_summaries = self._process_classes(all_classes, parsed_files)
        
        # Process interfaces
        interface_summaries = self._process_interfaces(all_interfaces)
        
        # Build final structure
        structured_knowledge = {
            "metadata": self._build_metadata(class_summaries, all_interfaces, packages),
            "project_overview": project_overview,
            "classes": class_summaries,
            "interfaces": interface_summaries
        }
        
        return structured_knowledge
    
    def _process_classes(self, all_classes: List[Dict[str, Any]], 
                        parsed_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all classes and generate summaries.
        
        Args:
            all_classes: List of all class information
            parsed_files: List of parsed files for package lookup
        
        Returns:
            List of processed class dictionaries
        """
        class_summaries = []
        
        for idx, cls in enumerate(all_classes, 1):
            logger.info(f"Processing class {idx}/{len(all_classes)}: {cls['name']}")
            
            # Extract summary using LLM
            summary = self.llm_service.extract_class_summary(cls)
            
            # Find package for this class
            package = self._find_package(cls["name"], parsed_files)
            
            class_summaries.append({
                "name": cls["name"],
                "type": cls.get("type", "class"),
                "package": package,
                "extends": cls.get("extends"),
                "implements": cls.get("implements", []),
                "modifiers": cls.get("modifiers", []),
                "method_count": cls.get("method_count", 0),
                "field_count": cls.get("field_count", 0),
                "avg_complexity": round(cls.get("avg_complexity", 0), 2),
                "methods": [
                    {
                        "name": m["name"],
                        "signature": m["signature"],
                        "complexity": m["complexity"],
                        "modifiers": m["modifiers"]
                    }
                    for m in cls.get("methods", [])
                ],
                "fields": cls.get("fields", []),
                "summary": summary
            })
        
        return class_summaries
    
    def _process_interfaces(self, all_interfaces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process all interfaces.
        
        Args:
            all_interfaces: List of all interface information
        
        Returns:
            List of processed interface dictionaries
        """
        interface_summaries = []
        
        for interface in all_interfaces:
            interface_summaries.append({
                "name": interface["name"],
                "type": "interface",
                "extends": interface.get("extends", []),
                "method_count": interface.get("method_count", 0),
                "methods": [
                    {
                        "name": m["name"],
                        "signature": m["signature"]
                    }
                    for m in interface.get("methods", [])
                ]
            })
        
        return interface_summaries
    
    def _find_package(self, class_name: str, parsed_files: List[Dict[str, Any]]) -> str:
        """
        Find package name for a given class.
        
        Args:
            class_name: Name of the class
            parsed_files: List of parsed files
        
        Returns:
            Package name or "N/A"
        """
        for pf in parsed_files:
            if any(c["name"] == class_name for c in pf["classes"]):
                return pf.get("package", "N/A")
        return "N/A"
    
    def _build_metadata(self, class_summaries: List[Dict[str, Any]], 
                       all_interfaces: List[Dict[str, Any]], 
                       packages: List[str]) -> Dict[str, Any]:
        """
        Build metadata section.
        
        Args:
            class_summaries: List of processed classes
            all_interfaces: List of interfaces
            packages: List of package names
        
        Returns:
            Metadata dictionary
        """
        total_methods = sum(c["method_count"] for c in class_summaries)
        avg_complexity = 0
        if class_summaries:
            avg_complexity = round(
                sum(c["avg_complexity"] for c in class_summaries) / len(class_summaries), 
                2
            )
        
        return {
            "extraction_date": datetime.now().isoformat(),
            "total_classes": len(class_summaries),
            "total_interfaces": len(all_interfaces),
            "total_methods": total_methods,
            "packages": list(set(packages)),
            "avg_class_complexity": avg_complexity
        }