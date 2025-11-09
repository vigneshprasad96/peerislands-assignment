import os
from typing import List, Dict, Any
from config import Config
from logger import logger
from java_parser import parse_java_file


class RepositoryScanner:
    """Scanner for Java repositories."""
    
    def __init__(self, repo_path: str = Config.REPO_PATH):
        """
        Initialize repository scanner.
        
        Args:
            repo_path: Path to repository to scan
        """
        self.repo_path = repo_path
    
    def scan(self) -> List[Dict[str, Any]]:
        """
        Scan repository and parse all Java files.
        
        Returns:
            List of parsed file data
        """
        logger.info(f"Scanning repository: {self.repo_path}")
        
        all_files = []
        java_files = []
        
        # Walk through directory tree
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                all_files.append(file)
                if any(file.endswith(ext) for ext in Config.FILE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    java_files.append(file_path)
        
        logger.info(f"Found {len(java_files)} Java files out of {len(all_files)} total files")
        
        # Parse each Java file
        parsed_files = []
        for idx, file_path in enumerate(java_files, 1):
            logger.info(f"Parsing {idx}/{len(java_files)}: {file_path}")
            parsed = parse_java_file(file_path)
            if parsed["classes"] or parsed["interfaces"]:
                parsed_files.append(parsed)
        
        logger.info(f"Successfully parsed {len(parsed_files)} files")
        return parsed_files
    
    def get_statistics(self, parsed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate repository statistics.
        
        Args:
            parsed_files: List of parsed file data
        
        Returns:
            Dictionary with statistics
        """
        all_classes = []
        all_interfaces = []
        packages = []
        
        for file_data in parsed_files:
            all_classes.extend(file_data["classes"])
            all_interfaces.extend(file_data["interfaces"])
            if file_data["package"]:
                packages.append(file_data["package"])
        
        total_methods = sum(c.get("method_count", 0) for c in all_classes)
        total_fields = sum(c.get("field_count", 0) for c in all_classes)
        
        return {
            "total_files": len(parsed_files),
            "total_classes": len(all_classes),
            "total_interfaces": len(all_interfaces),
            "total_methods": total_methods,
            "total_fields": total_fields,
            "unique_packages": len(set(packages)),
            "packages": list(set(packages))
        }