import json
import sys
from config import Config
from logger import logger
from git_cloner import GitCloner
from repository_scanner import RepositoryScanner
from llm_service import LLMService
from knowledge_structurer import KnowledgeStructurer
from vector_store import VectorStoreManager


def main():
    """Main execution flow."""
    try:
        # Validate configuration
        logger.info("=" * 80)
        logger.info("Java Codebase Knowledge Extractor")
        logger.info("=" * 80)
        Config.validate()
        
        # Clone repository if URL is provided
        if Config.REPO_URL:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 0: Cloning Repository")
            logger.info("=" * 80)
            
            # Initialize git cloner with token if available
            if Config.GIT_TOKEN:
                logger.info("Using Git Personal Access Token for authentication")
            else:
                logger.info("No Git token provided - using unauthenticated access")
                logger.info("Note: GitHub has rate limits for unauthenticated requests")
            
            git_cloner = GitCloner(Config.REPO_PATH, git_token=Config.GIT_TOKEN)
            
            try:
                git_cloner.clone_repository(Config.REPO_URL, force=Config.FORCE_CLONE)
                
                # Display repository info
                repo_info = git_cloner.get_repo_info()
                if repo_info:
                    logger.info("\nRepository Information:")
                    logger.info(f"  - Path: {repo_info['path']}")
                    logger.info(f"  - Remote URL: {repo_info['remote_url']}")
                    logger.info(f"  - Branch: {repo_info['branch']}")
                    logger.info(f"  - Latest Commit: {repo_info['latest_commit']['hash']}")
                    logger.info(f"  - Author: {repo_info['latest_commit']['author']}")
                    logger.info(f"  - Message: {repo_info['latest_commit']['message']}")
            except Exception as e:
                logger.error(f"Failed to clone repository: {e}")
                sys.exit(1)
        else:
            logger.info(f"Using existing repository at: {Config.REPO_PATH}")
        
        # Initialize services
        logger.info("\nInitializing services...")
        llm_service = LLMService()
        repository_scanner = RepositoryScanner()
        knowledge_structurer = KnowledgeStructurer(llm_service)
        vector_store_manager = VectorStoreManager()
        
        # Scan repository
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Scanning Repository")
        logger.info("=" * 80)
        parsed_files = repository_scanner.scan()
        
        if not parsed_files:
            logger.error("No Java files found or parsed successfully")
            sys.exit(1)
        
        # Display statistics
        stats = repository_scanner.get_statistics(parsed_files)
        logger.info("\nRepository Statistics:")
        logger.info(f"  - Total Files: {stats['total_files']}")
        logger.info(f"  - Total Classes: {stats['total_classes']}")
        logger.info(f"  - Total Interfaces: {stats['total_interfaces']}")
        logger.info(f"  - Total Methods: {stats['total_methods']}")
        logger.info(f"  - Total Fields: {stats['total_fields']}")
        logger.info(f"  - Unique Packages: {stats['unique_packages']}")
        
        # Structure knowledge
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Extracting and Structuring Knowledge")
        logger.info("=" * 80)
        structured_knowledge = knowledge_structurer.structure_knowledge(parsed_files)
        
        # Store in vector database
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Storing in Vector Database")
        logger.info("=" * 80)
        vector_store_manager.store_knowledge(structured_knowledge)
        
        # Save to JSON
        logger.info("\n" + "=" * 80)
        logger.info("STEP 4: Saving Results")
        logger.info("=" * 80)
        output_path = Config.OUTPUT_FILE
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(structured_knowledge, f, indent=2, ensure_ascii=False)
        
        # Display summary
        logger.info("\n" + "=" * 80)
        logger.info("✅ EXTRACTION COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"📄 Results saved to: {output_path}")
        logger.info(f"📊 Processed Classes: {structured_knowledge['metadata']['total_classes']}")
        logger.info(f"📦 Processed Interfaces: {structured_knowledge['metadata']['total_interfaces']}")
        logger.info(f"🔧 Total Methods: {structured_knowledge['metadata']['total_methods']}")
        logger.info(f"📁 Unique Packages: {len(structured_knowledge['metadata']['packages'])}")
        logger.info(f"⚙️  Average Complexity: {structured_knowledge['metadata']['avg_class_complexity']}")
        logger.info("=" * 80)
        
        return structured_knowledge
        
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\n❌ Error during execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()