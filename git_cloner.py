import os
import shutil
from typing import Optional
from git import Repo, GitCommandError
from logger import logger


class GitCloner:
    """Handles cloning of Git repositories with authentication support."""
    
    def __init__(self, target_dir: str = "cloned_code_repo", git_token: Optional[str] = None):
        """
        Initialize Git cloner.
        
        Args:
            target_dir: Directory where repository will be cloned
            git_token: Git Personal Access Token for authentication (optional)
        """
        self.target_dir = target_dir
        self.git_token = git_token
    
    def clone_repository(self, repo_url: str, force: bool = False) -> str:
        """
        Clone a Git repository to the target directory.
        
        Args:
            repo_url: Git repository URL (HTTPS or SSH)
            force: If True, remove existing directory before cloning
        
        Returns:
            Path to cloned repository
        
        Raises:
            GitCommandError: If cloning fails
            ValueError: If repo_url is invalid
        """
        if not repo_url:
            raise ValueError("Repository URL cannot be empty")
        
        logger.info(f"Cloning repository: {self._mask_url(repo_url)}")
        logger.info(f"Target directory: {self.target_dir}")
        
        # Check if directory exists
        if os.path.exists(self.target_dir):
            if force:
                logger.warning(f"Removing existing directory: {self.target_dir}")
                shutil.rmtree(self.target_dir)
            else:
                logger.info(f"Directory already exists: {self.target_dir}")
                if self._is_git_repo(self.target_dir):
                    logger.info("Using existing repository")
                    return self.target_dir
                else:
                    raise ValueError(
                        f"Directory {self.target_dir} exists but is not a git repository. "
                        f"Use force=True to remove it."
                    )
        
        # Inject token into URL if provided
        clone_url = self._inject_token(repo_url) if self.git_token else repo_url
        
        # Clone the repository
        try:
            logger.info("Starting clone operation...")
            
            # Set environment variables to avoid credential prompts
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            
            Repo.clone_from(clone_url, self.target_dir, env=env)
            logger.info(f"✅ Repository cloned successfully to {self.target_dir}")
            return self.target_dir
        except GitCommandError as e:
            error_msg = str(e)
            # Mask token in error messages
            if self.git_token:
                error_msg = error_msg.replace(self.git_token, "***TOKEN***")
            logger.error(f"Failed to clone repository: {error_msg}")
            
            # Provide helpful error messages
            if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                logger.error(
                    "Authentication required. Please provide a GIT_TOKEN in your .env file.\n"
                    "Create a token at: https://github.com/settings/tokens"
                )
            elif "Repository not found" in error_msg:
                logger.error(
                    "Repository not found. Check the URL or your access permissions."
                )
            elif "rate limit" in error_msg.lower():
                logger.error(
                    "GitHub API rate limit exceeded. Please provide a GIT_TOKEN to increase limits."
                )
            
            raise
    
    def _inject_token(self, repo_url: str) -> str:
        """
        Inject Git token into HTTPS URL for authentication.
        
        Args:
            repo_url: Original repository URL
        
        Returns:
            URL with embedded token
        """
        if not self.git_token:
            return repo_url
        
        # Only inject token for HTTPS URLs
        if repo_url.startswith("https://"):
            # Format: https://TOKEN@github.com/user/repo.git
            if "github.com" in repo_url:
                return repo_url.replace("https://", f"https://{self.git_token}@")
            elif "gitlab.com" in repo_url:
                return repo_url.replace("https://", f"https://oauth2:{self.git_token}@")
            else:
                # Generic HTTPS with token
                return repo_url.replace("https://", f"https://{self.git_token}@")
        
        # For SSH URLs, token is not used
        return repo_url
    
    def _mask_url(self, url: str) -> str:
        """
        Mask sensitive information in URL for logging.
        
        Args:
            url: URL to mask
        
        Returns:
            Masked URL
        """
        if self.git_token and self.git_token in url:
            return url.replace(self.git_token, "***TOKEN***")
        return url
    
    def _is_git_repo(self, path: str) -> bool:
        """
        Check if a directory is a valid git repository.
        
        Args:
            path: Directory path to check
        
        Returns:
            True if valid git repository, False otherwise
        """
        try:
            Repo(path)
            return True
        except Exception:
            return False
    
    def get_repo_info(self) -> Optional[dict]:
        """
        Get information about the cloned repository.
        
        Returns:
            Dictionary with repository information or None if not cloned
        """
        if not os.path.exists(self.target_dir):
            return None
        
        try:
            repo = Repo(self.target_dir)
            
            # Get remote URL (mask token if present)
            remote_url = None
            if repo.remotes:
                remote_url = self._mask_url(repo.remotes.origin.url)
            
            # Get current branch
            branch = repo.active_branch.name if not repo.head.is_detached else "detached"
            
            # Get latest commit
            latest_commit = repo.head.commit
            
            # Count total commits
            commit_count = sum(1 for _ in repo.iter_commits())
            
            return {
                "path": self.target_dir,
                "remote_url": remote_url,
                "branch": branch,
                "commit_count": commit_count,
                "latest_commit": {
                    "hash": latest_commit.hexsha[:8],
                    "author": str(latest_commit.author),
                    "message": latest_commit.message.strip(),
                    "date": latest_commit.committed_datetime.isoformat()
                }
            }
        except Exception as e:
            logger.warning(f"Could not get repository info: {e}")
            return None
    
    def pull_latest(self) -> bool:
        """
        Pull latest changes from remote repository.
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.target_dir):
            logger.error("Repository not cloned yet")
            return False
        
        try:
            repo = Repo(self.target_dir)
            origin = repo.remotes.origin
            logger.info("Pulling latest changes...")
            
            # Set environment to avoid prompts
            env = os.environ.copy()
            env['GIT_TERMINAL_PROMPT'] = '0'
            
            origin.pull(env=env)
            logger.info("✅ Repository updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to pull latest changes: {e}")
            return False
    
    def cleanup(self) -> bool:
        """
        Remove the cloned repository directory.
        
        Returns:
            True if successful, False otherwise
        """
        if os.path.exists(self.target_dir):
            try:
                logger.info(f"Removing directory: {self.target_dir}")
                shutil.rmtree(self.target_dir)
                logger.info("✅ Directory removed successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to remove directory: {e}")
                return False
        return True