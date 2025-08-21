#!/usr/bin/env python3
"""
GitHub Monorepo Splitter AI Agent

This agent automatically splits a GitHub monorepo into multiple repositories,
preserving git history for each project and common libraries.

Supports two modes:
1. Branch-based splitting (original functionality)
2. Project-based splitting (new functionality for same-branch projects with shared libraries)

Usage:
    python split_repo_agent.py [--dry-run] [--mode branch|project]

Requirements:
    - git-filter-repo installed and available in PATH
    - GitHub Personal Access Token with repo scope
    - Python 3.9+
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime

import requests
from dotenv import load_dotenv
from github import Github, GithubException


@dataclass
class RepoSplitterConfig:
    """Configuration for the repository splitter."""
    source_repo_url: str
    mode: str  # 'branch' or 'project'
    branches: Optional[List[str]] = None
    projects: Optional[List[str]] = None
    common_path: Optional[str] = None
    org: str = ""
    github_token: str = ""
    dry_run: bool = False


class RepoSplitter:
    """Main class for splitting GitHub monorepos into multiple repositories."""
    
    def __init__(self, config: RepoSplitterConfig):
        self.config = config
        self.github = Github(config.github_token)
        self.temp_dir = None
        self.source_repo_path = None
        self.created_repos = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('repo_splitter.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        self.cleanup()
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            self.logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def load_config(self) -> RepoSplitterConfig:
        """Load configuration from environment variables."""
        load_dotenv()
        
        mode = os.getenv('MODE', 'branch').lower()
        
        if mode == 'branch':
            branches = os.getenv('BRANCHES', '').split(',')
            branches = [branch.strip() for branch in branches if branch.strip()]
            config = RepoSplitterConfig(
                source_repo_url=os.getenv('SOURCE_REPO_URL', ''),
                mode=mode,
                branches=branches,
                common_path=os.getenv('COMMON_PATH'),
                org=os.getenv('ORG', ''),
                github_token=os.getenv('GITHUB_TOKEN', ''),
                dry_run=False
            )
        elif mode == 'project':
            projects = os.getenv('PROJECTS', '').split(',')
            projects = [project.strip() for project in projects if project.strip()]
            config = RepoSplitterConfig(
                source_repo_url=os.getenv('SOURCE_REPO_URL', ''),
                mode=mode,
                projects=projects,
                common_path=os.getenv('COMMON_PATH'),
                org=os.getenv('ORG', ''),
                github_token=os.getenv('GITHUB_TOKEN', ''),
                dry_run=False
            )
        else:
            raise ValueError("MODE must be either 'branch' or 'project'")
        
        # Validate required fields
        if not config.source_repo_url:
            raise ValueError("SOURCE_REPO_URL is required")
        if not config.org:
            raise ValueError("ORG is required")
        if not config.github_token:
            raise ValueError("GITHUB_TOKEN is required")
        
        if mode == 'branch' and not config.branches:
            raise ValueError("BRANCHES is required for branch mode")
        elif mode == 'project' and not config.projects:
            raise ValueError("PROJECTS is required for project mode")
        
        self.logger.info(f"Configuration loaded: mode={mode}, org={config.org}")
        if mode == 'branch':
            self.logger.info(f"Branches: {len(config.branches)}")
        else:
            self.logger.info(f"Projects: {len(config.projects)}")
        
        return config
    
    def run_git_command(self, command: List[str], cwd: str = None, check: bool = True) -> subprocess.CompletedProcess:
        """Run a git command and return the result."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Git command failed: {' '.join(command)}")
            self.logger.error(f"Error: {e.stderr}")
            raise
    
    def clone_source_repo(self) -> str:
        """Clone the source repository to a temporary directory."""
        self.temp_dir = tempfile.mkdtemp(prefix="repo_splitter_")
        self.source_repo_path = os.path.join(self.temp_dir, "source_repo")
        
        self.logger.info(f"Cloning source repository: {self.config.source_repo_url}")
        self.logger.info(f"Temporary directory: {self.temp_dir}")
        
        if not self.config.dry_run:
            self.run_git_command([
                'git', 'clone', '--mirror', self.config.source_repo_url, self.source_repo_path
            ])
        
        return self.source_repo_path
    
    def create_github_repo(self, repo_name: str, description: str = "") -> Optional[str]:
        """Create a new GitHub repository via API."""
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would create repo: {repo_name}")
            return f"https://github.com/{self.config.org}/{repo_name}.git"
        
        try:
            # Check if repo already exists
            try:
                existing_repo = self.github.get_repo(f"{self.config.org}/{repo_name}")
                self.logger.warning(f"Repository {repo_name} already exists, skipping creation")
                return existing_repo.clone_url
            except GithubException:
                pass
            
            # Create new repository
            if '/' in self.config.org:
                # Organization
                org = self.github.get_organization(self.config.org)
                repo = org.create_repo(
                    name=repo_name,
                    description=description,
                    private=False,
                    auto_init=False
                )
            else:
                # User
                user = self.github.get_user()
                repo = user.create_repo(
                    name=repo_name,
                    description=description,
                    private=False,
                    auto_init=False
                )
            
            self.logger.info(f"Created repository: {repo_name}")
            self.created_repos.append(repo_name)
            return repo.clone_url
            
        except GithubException as e:
            self.logger.error(f"Failed to create repository {repo_name}: {e}")
            return None
    
    def extract_branch_to_repo(self, branch_name: str, repo_name: str, repo_url: str):
        """Extract a single branch to a new repository."""
        branch_repo_path = os.path.join(self.temp_dir, f"branch_{branch_name}")
        
        self.logger.info(f"Extracting branch '{branch_name}' to repository '{repo_name}'")
        
        if not self.config.dry_run:
            # Clone the mirror repo
            self.run_git_command(['git', 'clone', self.source_repo_path, branch_repo_path])
            
            # Change to the branch repository directory
            os.chdir(branch_repo_path)
            
            # Fetch all branches
            self.run_git_command(['git', 'fetch', 'origin'])
            
            # Checkout the specific branch
            self.run_git_command(['git', 'checkout', branch_name])
            
            # Create a new branch from the current state
            self.run_git_command(['git', 'checkout', '-b', 'temp_branch'])
            
            # Remove all other branches except the current one
            self.run_git_command(['git', 'branch', '-D', branch_name])
            
            # Check if main branch exists and handle it
            try:
                # Try to rename temp_branch to main
                self.run_git_command(['git', 'branch', '-m', 'temp_branch', 'main'])
            except subprocess.CalledProcessError:
                # If main already exists, delete it first
                self.logger.info("Main branch already exists, removing it first")
                self.run_git_command(['git', 'branch', '-D', 'main'])
                self.run_git_command(['git', 'branch', '-m', 'temp_branch', 'main'])
            
            # Remove remote origin
            self.run_git_command(['git', 'remote', 'remove', 'origin'])
            
            # Add new remote
            self.run_git_command(['git', 'remote', 'add', 'origin', repo_url])
            
            # Push to the new repository
            self.run_git_command(['git', 'push', '-u', 'origin', 'main'])
            
            self.logger.info(f"Successfully extracted branch '{branch_name}' to '{repo_name}'")
    
    def extract_project_to_repo(self, project_name: str, repo_name: str, repo_url: str):
        """Extract a single project to a new repository using git filter-repo."""
        project_repo_path = os.path.join(self.temp_dir, f"project_{project_name}")
        
        self.logger.info(f"Extracting project '{project_name}' to repository '{repo_name}'")
        
        if not self.config.dry_run:
            # Clone the mirror repo
            self.run_git_command(['git', 'clone', self.source_repo_path, project_repo_path])
            
            # Change to the project repo directory
            os.chdir(project_repo_path)
            
            # Check if the project directory exists in the repository
            if not os.path.exists(project_name):
                self.logger.warning(f"Project directory '{project_name}' not found in repository")
                return
            
            # Use git filter-repo to extract only the project path
            # Move everything from project_name/ to the root
            self.run_git_command([
                'git', 'filter-repo',
                '--path', f'{project_name}/',
                '--path-rename', f'{project_name}/:',
                '--force'
            ])
            
            # Check if main branch exists after filtering
            result = self.run_git_command(['git', 'branch', '--list', 'main'], check=False)
            if not result.stdout.strip():
                # No main branch, create one from the current HEAD
                self.logger.info("No main branch found after filtering, creating one")
                self.run_git_command(['git', 'checkout', '-b', 'main'])
            
            # Remove remote origin if it exists
            try:
                self.run_git_command(['git', 'remote', 'remove', 'origin'])
            except subprocess.CalledProcessError:
                # Remote doesn't exist, which is fine
                pass
            
            # Add new remote
            self.run_git_command(['git', 'remote', 'add', 'origin', repo_url])
            
            # Push to the new repository
            self.run_git_command(['git', 'push', '-u', 'origin', 'main'])
            
            self.logger.info(f"Successfully extracted project '{project_name}' to '{repo_name}'")
    
    def extract_common_libs(self, repo_name: str, repo_url: str):
        """Extract common libraries to a separate repository using git filter-repo."""
        if not self.config.common_path:
            self.logger.info("No common path specified, skipping common libraries extraction")
            return
        
        common_repo_path = os.path.join(self.temp_dir, "common_libs")
        
        self.logger.info(f"Extracting common libraries from '{self.config.common_path}' to '{repo_name}'")
        
        if not self.config.dry_run:
            # Clone the mirror repo
            self.run_git_command(['git', 'clone', self.source_repo_path, common_repo_path])
            
            # Change to the common repo directory
            os.chdir(common_repo_path)
            
            # Use git filter-repo to extract only the common path
            self.run_git_command([
                'git', 'filter-repo',
                '--path', f'{self.config.common_path}/',
                '--path-rename', f'{self.config.common_path}/:',
                '--force'
            ])
            
            # Check if main branch exists after filtering
            result = self.run_git_command(['git', 'branch', '--list', 'main'], check=False)
            if not result.stdout.strip():
                # No main branch, create one from the current HEAD
                self.logger.info("No main branch found after filtering, creating one")
                self.run_git_command(['git', 'checkout', '-b', 'main'])
            
            # Remove remote origin if it exists
            try:
                self.run_git_command(['git', 'remote', 'remove', 'origin'])
            except subprocess.CalledProcessError:
                # Remote doesn't exist, which is fine
                pass
            
            # Add new remote
            self.run_git_command(['git', 'remote', 'add', 'origin', repo_url])
            
            # Push to the new repository
            self.run_git_command(['git', 'push', '-u', 'origin', 'main'])
            
            self.logger.info(f"Successfully extracted common libraries to '{repo_name}'")
    
    def analyze_common_files(self) -> Dict[str, List[str]]:
        """Analyze branches/projects to suggest common files (AI extension)."""
        self.logger.info("Analyzing for common files...")
        
        common_files = {}
        
        if not self.config.dry_run:
            if self.config.mode == 'branch':
                # Get all branches
                os.chdir(self.source_repo_path)
                result = self.run_git_command(['git', 'branch', '-r'])
                all_branches = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                
                # For each branch, get the file tree
                for branch in self.config.branches:
                    branch_ref = f"origin/{branch}"
                    if branch_ref in all_branches:
                        result = self.run_git_command(['git', 'ls-tree', '-r', '--name-only', branch_ref])
                        files = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                        common_files[branch] = files
            else:
                # For project mode, analyze current directory structure
                os.chdir(self.source_repo_path)
                for project in self.config.projects:
                    if os.path.exists(project):
                        project_files = []
                        for root, dirs, files in os.walk(project):
                            for file in files:
                                rel_path = os.path.relpath(os.path.join(root, file), '.')
                                project_files.append(rel_path)
                        common_files[project] = project_files
            
            # Find common files across branches/projects
            if len(common_files) > 1:
                all_files = set(list(common_files.values())[0])
                for files in list(common_files.values())[1:]:
                    all_files = all_files.intersection(set(files))
                
                if all_files:
                    self.logger.info(f"Found {len(all_files)} common files across all branches/projects")
                    self.logger.info(f"Common files: {list(all_files)[:10]}...")  # Show first 10
        
        return common_files
    
    def split_repositories(self):
        """Main method to split the monorepo into multiple repositories."""
        try:
            # Load configuration
            self.config = self.load_config()
            
            # Clone source repository
            self.clone_source_repo()
            
            # Analyze common files (optional AI extension)
            self.analyze_common_files()
            
            if self.config.mode == 'branch':
                # Process each branch
                for branch in self.config.branches:
                    repo_name = f"{branch}-app"
                    description = f"Application extracted from {branch} branch of monorepo"
                    
                    self.logger.info(f"Processing branch: {branch}")
                    
                    # Create GitHub repository
                    repo_url = self.create_github_repo(repo_name, description)
                    if repo_url:
                        # Extract branch to new repository
                        self.extract_branch_to_repo(branch, repo_name, repo_url)
                        self.logger.info(f"Repository URL: {repo_url}")
                    else:
                        self.logger.error(f"Failed to create repository for branch: {branch}")
            
            else:  # project mode
                # Process each project
                for project in self.config.projects:
                    repo_name = f"{project}-app"
                    description = f"Application extracted from {project} project of monorepo"
                    
                    self.logger.info(f"Processing project: {project}")
                    
                    # Create GitHub repository
                    repo_url = self.create_github_repo(repo_name, description)
                    if repo_url:
                        # Extract project to new repository
                        self.extract_project_to_repo(project, repo_name, repo_url)
                        self.logger.info(f"Repository URL: {repo_url}")
                    else:
                        self.logger.error(f"Failed to create repository for project: {project}")
            
            # Process common libraries
            if self.config.common_path:
                repo_name = "common-libs"
                description = f"Common libraries extracted from {self.config.common_path}"
                
                self.logger.info(f"Processing common libraries from: {self.config.common_path}")
                
                # Create GitHub repository
                repo_url = self.create_github_repo(repo_name, description)
                if repo_url:
                    # Extract common libraries
                    self.extract_common_libs(repo_name, repo_url)
                    self.logger.info(f"Common libraries repository URL: {repo_url}")
                else:
                    self.logger.error("Failed to create common libraries repository")
            
            # Summary
            self.logger.info("=" * 50)
            self.logger.info("REPOSITORY SPLITTING COMPLETED")
            self.logger.info("=" * 50)
            self.logger.info(f"Created {len(self.created_repos)} repositories:")
            for repo in self.created_repos:
                self.logger.info(f"  - {repo}")
            
            if self.config.dry_run:
                self.logger.info("This was a dry run - no actual changes were made")
            
        except Exception as e:
            self.logger.error(f"Error during repository splitting: {e}")
            raise


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Split GitHub monorepo into multiple repositories")
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--mode', choices=['branch', 'project'], default='branch', 
                       help='Splitting mode: branch (different branches) or project (same branch, different projects)')
    args = parser.parse_args()
    
    try:
        # Load configuration from environment first
        load_dotenv()
        
        # Override mode if specified in command line
        mode = args.mode
        if os.getenv('MODE'):
            mode = os.getenv('MODE').lower()
        
        if mode == 'branch':
            branches = os.getenv('BRANCHES', '').split(',')
            branches = [branch.strip() for branch in branches if branch.strip()]
            config = RepoSplitterConfig(
                source_repo_url=os.getenv('SOURCE_REPO_URL', ''),
                mode=mode,
                branches=branches,
                common_path=os.getenv('COMMON_PATH'),
                org=os.getenv('ORG', ''),
                github_token=os.getenv('GITHUB_TOKEN', ''),
                dry_run=args.dry_run
            )
        else:  # project mode
            projects = os.getenv('PROJECTS', '').split(',')
            projects = [project.strip() for project in projects if project.strip()]
            config = RepoSplitterConfig(
                source_repo_url=os.getenv('SOURCE_REPO_URL', ''),
                mode=mode,
                projects=projects,
                common_path=os.getenv('COMMON_PATH'),
                org=os.getenv('ORG', ''),
                github_token=os.getenv('GITHUB_TOKEN', ''),
                dry_run=args.dry_run
            )
        
        # Validate required fields
        if not config.source_repo_url:
            raise ValueError("SOURCE_REPO_URL is required")
        if not config.org:
            raise ValueError("ORG is required")
        if not config.github_token:
            raise ValueError("GITHUB_TOKEN is required")
        
        if mode == 'branch' and not config.branches:
            raise ValueError("BRANCHES is required for branch mode")
        elif mode == 'project' and not config.projects:
            raise ValueError("PROJECTS is required for project mode")
        
        with RepoSplitter(config) as splitter:
            splitter.split_repositories()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
