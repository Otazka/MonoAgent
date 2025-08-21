#!/usr/bin/env python3
"""
Advanced GitHub Monorepo Splitter AI Agent

This AI agent intelligently analyzes and splits GitHub monorepos into multiple repositories,
handling complex scenarios:

1. Different apps on the same branch → Separate into different repos
2. Common/generic components → Separate into shared library repos  
3. Different apps on separate branches → Each app gets its own repo
4. Intelligent project structure detection and analysis

Usage:
    python split_repo_agent.py [--dry-run] [--analyze-only]

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
import re
from pathlib import Path
from typing import List, Dict, Optional, Union, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import time

import requests
from dotenv import load_dotenv
from github import Github, GithubException


@dataclass
class ProjectInfo:
    """Information about a detected project/app."""
    name: str
    path: str
    type: str  # 'app', 'library', 'service', 'frontend', 'backend', etc.
    dependencies: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    size: int = 0
    description: str = ""


@dataclass
class CommonComponent:
    """Information about common/shared components."""
    name: str
    path: str
    usage_count: int = 0
    used_by: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)


@dataclass
class RepoSplitterConfig:
    """Configuration for the repository splitter."""
    source_repo_url: str
    org: str
    github_token: str
    dry_run: bool = False
    analyze_only: bool = False
    auto_detect: bool = True
    manual_projects: Optional[List[str]] = None
    manual_common_paths: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    # New universal options
    mode: str = "auto"  # auto | project | branch
    branches: Optional[List[str]] = None
    common_path: Optional[str] = None
    repo_name_template_app: str = "{name}-app"
    repo_name_template_lib: str = "{name}-lib"
    default_branch: str = "main"
    private_repos: bool = False


class MonorepoAnalyzer:
    """AI-powered analyzer for monorepo structure detection."""
    
    def __init__(self, repo_path: str, logger: logging.Logger):
        self.repo_path = repo_path
        self.logger = logger
        self.projects: Dict[str, ProjectInfo] = {}
        self.common_components: Dict[str, CommonComponent] = {}
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
        
    def analyze_repository_structure(self) -> Tuple[Dict[str, ProjectInfo], Dict[str, CommonComponent]]:
        """Analyze the monorepo structure to detect projects and common components."""
        self.logger.info("🔍 Starting AI-powered monorepo analysis...")
        
        # Get all files and directories
        all_files = self._get_all_files()
        
        # Detect project structure
        self._detect_projects(all_files)
        
        # Detect common components
        self._detect_common_components(all_files)
        
        # Analyze dependencies
        self._analyze_dependencies()
        
        # Generate report
        self._generate_analysis_report()
        
        return self.projects, self.common_components
    
    def _get_all_files(self) -> List[str]:
        """Get all files in the repository."""
        files = []
        for root, dirs, filenames in os.walk(self.repo_path):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, self.repo_path)
                files.append(rel_path)
        
        return files
    
    def _detect_projects(self, all_files: List[str]):
        """Detect individual projects/apps in the monorepo."""
        self.logger.info("📁 Detecting projects and applications...")
        
        # Common project indicators
        project_indicators = {
            'package.json': 'nodejs',
            'requirements.txt': 'python',
            'pom.xml': 'java',
            'build.gradle': 'java',
            'Cargo.toml': 'rust',
            'go.mod': 'go',
            'composer.json': 'php',
            'Gemfile': 'ruby',
            'Dockerfile': 'docker',
            'docker-compose.yml': 'docker',
            'Makefile': 'make',
            'CMakeLists.txt': 'cmake',
            'pubspec.yaml': 'flutter',
            'angular.json': 'angular',
            'vue.config.js': 'vue',
            'next.config.js': 'nextjs',
            'nuxt.config.js': 'nuxt',
            'vite.config.js': 'vite',
            'webpack.config.js': 'webpack',
            'rollup.config.js': 'rollup',
            'tsconfig.json': 'typescript',
            'app.json': 'react-native',
            'project.json': 'nx',
            'workspace.json': 'nx',
            'lerna.json': 'lerna',
            'rush.json': 'rush',
            'pnpm-workspace.yaml': 'pnpm',
            'yarn.lock': 'yarn',
            'package-lock.json': 'npm'
        }
        
        # Group files by directory
        dir_files = defaultdict(list)
        for file_path in all_files:
            dir_path = os.path.dirname(file_path)
            dir_files[dir_path].append(file_path)
        
        # Detect projects based on indicators
        for dir_path, files in dir_files.items():
            for file_name in files:
                if file_name in project_indicators:
                    project_type = project_indicators[file_name]
                    project_name = self._extract_project_name(dir_path, file_name)
                    
                    if project_name not in self.projects:
                        self.projects[project_name] = ProjectInfo(
                            name=project_name,
                            path=dir_path,
                            type=project_type,
                            files=files,
                            size=len(files)
                        )
                        self.logger.info(f"  ✅ Detected {project_type} project: {project_name} at {dir_path}")
                    break
        
        # Detect additional projects based on directory structure
        self._detect_by_directory_structure(all_files)
    
    def _extract_project_name(self, dir_path: str, config_file: str) -> str:
        """Extract a meaningful project name from directory path and config file."""
        if dir_path == '.' or dir_path == '':
            # Root level project
            return os.path.splitext(config_file)[0]
        
        # Use the last directory name
        return os.path.basename(dir_path)
    
    def _detect_by_directory_structure(self, all_files: List[str]):
        """Detect projects based on common directory patterns."""
        # Common app/service directory patterns
        app_patterns = [
            r'apps?/([^/]+)',
            r'services?/([^/]+)',
            r'frontend/([^/]+)',
            r'backend/([^/]+)',
            r'clients?/([^/]+)',
            r'packages?/([^/]+)',
            r'modules?/([^/]+)',
            r'components?/([^/]+)',
            r'features?/([^/]+)',
            r'projects?/([^/]+)'
        ]
        
        for file_path in all_files:
            for pattern in app_patterns:
                match = re.search(pattern, file_path)
                if match:
                    project_name = match.group(1)
                    if project_name not in self.projects:
                        # Check if this directory has substantial content
                        dir_path = os.path.dirname(file_path)
                        if self._is_substantial_project(dir_path, all_files):
                            self.projects[project_name] = ProjectInfo(
                                name=project_name,
                                path=dir_path,
                                type='app',
                                files=[f for f in all_files if f.startswith(dir_path)],
                                size=len([f for f in all_files if f.startswith(dir_path)])
                            )
                            self.logger.info(f"  ✅ Detected app project: {project_name} at {dir_path}")
                    break
    
    def _is_substantial_project(self, dir_path: str, all_files: List[str]) -> bool:
        """Check if a directory contains a substantial project."""
        project_files = [f for f in all_files if f.startswith(dir_path)]
        
        # Count source files
        source_extensions = {'.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rs', '.php', '.rb', '.cs', '.swift', '.kt'}
        source_files = [f for f in project_files if any(f.endswith(ext) for ext in source_extensions)]
        
        # Consider it substantial if it has multiple source files or config files
        return len(source_files) > 3 or any(f.endswith(('.json', '.yaml', '.yml', '.toml', '.xml')) for f in project_files)
    
    def _detect_common_components(self, all_files: List[str]):
        """Detect common/shared components and libraries."""
        self.logger.info("🔧 Detecting common components and shared libraries...")
        
        # Common library/shared component patterns
        common_patterns = [
            r'common/([^/]+)',
            r'shared/([^/]+)',
            r'libs?/([^/]+)',
            r'utils?/([^/]+)',
            r'core/([^/]+)',
            r'base/([^/]+)',
            r'foundation/([^/]+)',
            r'components?/([^/]+)',
            r'packages?/([^/]+)',
            r'modules?/([^/]+)'
        ]
        
        for file_path in all_files:
            for pattern in common_patterns:
                match = re.search(pattern, file_path)
                if match:
                    component_name = match.group(1)
                    if component_name not in self.common_components:
                        dir_path = os.path.dirname(file_path)
                        component_files = [f for f in all_files if f.startswith(dir_path)]
                        
                        self.common_components[component_name] = CommonComponent(
                            name=component_name,
                            path=dir_path,
                            files=component_files
                        )
                        self.logger.info(f"  ✅ Detected common component: {component_name} at {dir_path}")
                    break
    
    def _analyze_dependencies(self):
        """Analyze dependencies between projects and components."""
        self.logger.info("🔗 Analyzing dependencies between projects...")
        
        for project_name, project in self.projects.items():
            for file_path in project.files:
                if file_path.endswith(('.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go')):
                    dependencies = self._extract_dependencies(file_path)
                    project.dependencies.extend(dependencies)
            
            # Remove duplicates
            project.dependencies = list(set(project.dependencies))
    
    def _extract_dependencies(self, file_path: str) -> List[str]:
        """Extract dependencies from a source file."""
        dependencies = []
        
        try:
            full_path = os.path.join(self.repo_path, file_path)
            if os.path.exists(full_path):
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Look for import statements
                import_patterns = [
                    r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
                    r'require\s*\(\s*[\'"]([^\'"]+)[\'"]',
                    r'from\s+[\'"]([^\'"]+)[\'"]',
                    r'import\s+[\'"]([^\'"]+)[\'"]'
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    dependencies.extend(matches)
        except Exception as e:
            self.logger.debug(f"Could not analyze dependencies for {file_path}: {e}")
        
        return dependencies
    
    def _generate_analysis_report(self):
        """Generate a comprehensive analysis report."""
        self.logger.info("📊 Generating analysis report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_projects': len(self.projects),
            'total_common_components': len(self.common_components),
            'projects': {},
            'common_components': {},
            'recommendations': []
        }
        
        # Add project details
        for name, project in self.projects.items():
            report['projects'][name] = {
                'path': project.path,
                'type': project.type,
                'size': project.size,
                'dependencies': project.dependencies
            }
        
        # Add common component details
        for name, component in self.common_components.items():
            report['common_components'][name] = {
                'path': component.path,
                'files': len(component.files),
                'usage_count': component.usage_count
            }
        
        # Generate recommendations
        recommendations = []
        
        if len(self.projects) > 1:
            recommendations.append(f"Split {len(self.projects)} detected projects into separate repositories")
        
        if self.common_components:
            recommendations.append(f"Extract {len(self.common_components)} common components into shared libraries")
        
        if len(self.projects) > 5:
            recommendations.append("Consider creating a shared library for common utilities")
        
        report['recommendations'] = recommendations
        
        # Save report
        report_path = os.path.join(os.getcwd(), 'monorepo_analysis.json')
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📄 Analysis report saved to: {report_path}")
        
        # Print summary
        self.logger.info("=" * 60)
        self.logger.info("📋 MONOREPO ANALYSIS SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"🔍 Detected {len(self.projects)} projects:")
        for name, project in self.projects.items():
            self.logger.info(f"  • {name} ({project.type}) at {project.path}")
        
        self.logger.info(f"🔧 Detected {len(self.common_components)} common components:")
        for name, component in self.common_components.items():
            self.logger.info(f"  • {name} at {component.path}")
        
        self.logger.info("💡 Recommendations:")
        for rec in recommendations:
            self.logger.info(f"  • {rec}")


class RepoSplitter:
    """Advanced repository splitter with AI-powered analysis."""
    
    def __init__(self, config: RepoSplitterConfig):
        self.config = config
        self.github = Github(config.github_token)
        self.temp_dir = None
        self.source_repo_path = None
        self.created_repos = []
        self.analyzer = None
        
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
        
        # Load from environment first
        env_mode = os.getenv('MODE', 'auto').strip().lower()
        env_branches = os.getenv('BRANCHES')
        env_projects = os.getenv('PROJECTS')
        env_common_path = os.getenv('COMMON_PATH')
        env_private = os.getenv('PRIVATE_REPOS', 'false').lower() == 'true'
        env_default_branch = os.getenv('DEFAULT_BRANCH', 'main')
        env_tmpl_app = os.getenv('REPO_NAME_TEMPLATE_APP', '{name}-app')
        env_tmpl_lib = os.getenv('REPO_NAME_TEMPLATE_LIB', '{name}-lib')

        config = RepoSplitterConfig(
            source_repo_url=os.getenv('SOURCE_REPO_URL', ''),
            org=os.getenv('ORG', ''),
            github_token=os.getenv('GITHUB_TOKEN', ''),
            dry_run=self.config.dry_run,
            analyze_only=self.config.analyze_only,
            auto_detect=os.getenv('AUTO_DETECT', 'true').lower() == 'true',
            manual_projects=(os.getenv('MANUAL_PROJECTS', '').split(',') if os.getenv('MANUAL_PROJECTS') else (
                [p.strip() for p in env_projects.split(',')] if env_projects else None
            )),
            manual_common_paths=os.getenv('MANUAL_COMMON_PATHS', '').split(',') if os.getenv('MANUAL_COMMON_PATHS') else None,
            exclude_patterns=os.getenv('EXCLUDE_PATTERNS', '').split(',') if os.getenv('EXCLUDE_PATTERNS') else None,
            mode=env_mode,
            branches=([b.strip() for b in env_branches.split(',')] if env_branches else None),
            common_path=(env_common_path.strip() if env_common_path else None),
            repo_name_template_app=env_tmpl_app,
            repo_name_template_lib=env_tmpl_lib,
            default_branch=env_default_branch,
            private_repos=env_private
        )
        
        # Validate required fields
        if not config.source_repo_url:
            raise ValueError("SOURCE_REPO_URL is required")
        if not config.org:
            raise ValueError("ORG is required")
        if not config.github_token:
            raise ValueError("GITHUB_TOKEN is required")
        
        # CLI overrides (self.config may carry explicit flags)
        if getattr(self.config, 'mode', None):
            config.mode = self.config.mode
        if getattr(self.config, 'branches', None):
            config.branches = self.config.branches
        if getattr(self.config, 'manual_projects', None):
            config.manual_projects = self.config.manual_projects
        if getattr(self.config, 'common_path', None):
            config.common_path = self.config.common_path
        if getattr(self.config, 'repo_name_template_app', None):
            config.repo_name_template_app = self.config.repo_name_template_app
        if getattr(self.config, 'repo_name_template_lib', None):
            config.repo_name_template_lib = self.config.repo_name_template_lib
        if getattr(self.config, 'default_branch', None):
            config.default_branch = self.config.default_branch
        if getattr(self.config, 'private_repos', None) is not None:
            config.private_repos = self.config.private_repos

        self.logger.info(
            f"Configuration loaded: org={config.org}, mode={config.mode}, auto_detect={config.auto_detect}"
        )
        return config

    def _sanitize_repo_name(self, raw_name: str) -> str:
        """Sanitize a repository name to be GitHub-compatible and consistent."""
        name = raw_name.strip().lower()
        name = re.sub(r"[^a-z0-9._-]", "-", name)
        name = re.sub(r"-+", "-", name)
        name = name.strip("-._")
        return name or "repo"
    
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
        # Always clone for analysis and local filtering (safe in dry-run)
        self.run_git_command([
            'git', 'clone', '--mirror', self.config.source_repo_url, self.source_repo_path
        ])
        
        return self.source_repo_path
    
    def analyze_monorepo(self) -> Tuple[Dict[str, ProjectInfo], Dict[str, CommonComponent]]:
        """Analyze the monorepo structure using AI-powered detection."""
        self.logger.info("🤖 Starting AI-powered monorepo analysis...")
        
        # Clone the repository
        self.clone_source_repo()
        
        # Create analyzer
        self.analyzer = MonorepoAnalyzer(self.source_repo_path, self.logger)
        
        # Perform analysis
        projects, common_components = self.analyzer.analyze_repository_structure()
        
        return projects, common_components
    
    def create_github_repo(self, repo_name: str, description: str = "") -> Optional[str]:
        """Create a new GitHub repository via API."""
        # Sanitize name early for consistent logs
        repo_name = self._sanitize_repo_name(repo_name)
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would create repo: {repo_name}")
            return f"https://github.com/{self.config.org}/{repo_name}.git"
        
        last_exc: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                # Check if repo already exists
                try:
                    existing_repo = self.github.get_repo(f"{self.config.org}/{repo_name}")
                    self.logger.warning(f"Repository {repo_name} already exists, skipping creation")
                    return existing_repo.clone_url
                except GithubException:
                    pass
                
                # Try as organization first; fallback to user
                try:
                    org = self.github.get_organization(self.config.org)
                    repo = org.create_repo(
                        name=repo_name,
                        description=description,
                        private=self.config.private_repos,
                        auto_init=False
                    )
                except GithubException:
                    user = self.github.get_user()
                    repo = user.create_repo(
                        name=repo_name,
                        description=description,
                        private=self.config.private_repos,
                        auto_init=False
                    )
                
                self.logger.info(f"Created repository: {repo_name}")
                self.created_repos.append(repo_name)
                return repo.clone_url
            except GithubException as e:
                last_exc = e
                self.logger.warning(f"GitHub API error creating {repo_name} (attempt {attempt}/3): {e}")
                time.sleep(min(2 ** attempt, 8))
        
        self.logger.error(f"Failed to create repository {repo_name}: {last_exc}")
        return None
    
    def extract_project_to_repo(self, project: ProjectInfo, repo_name: str, repo_url: str):
        """Extract a project to its own repository."""
        project_repo_path = os.path.join(self.temp_dir, f"project_{project.name}")
        
        self.logger.info(f"Extracting project '{project.name}' to repository '{repo_name}'")
        
        if not self.config.dry_run:
            # Clone the mirror repo
            self.run_git_command(['git', 'clone', self.source_repo_path, project_repo_path])
            
            # Validate project path exists
            target_path = os.path.join(project_repo_path, project.path)
            if not os.path.exists(target_path):
                self.logger.error(f"Project path does not exist in repo: {project.path}")
                return
            
            # Use git filter-repo to extract only the project path
            self.run_git_command([
                'git', 'filter-repo',
                '--path', project.path,
                '--path-rename', f'{project.path}:',
                '--force'
            ], cwd=project_repo_path)
            
            # Remove remote origin
            self.run_git_command(['git', 'remote', 'remove', 'origin'], cwd=project_repo_path)
            
            # Add new remote
            self.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=project_repo_path)
            
            # Ensure default branch name
            self.run_git_command(['git', 'branch', '-M', self.config.default_branch], cwd=project_repo_path)
            # Push to the new repository
            self.run_git_command(['git', 'push', '-u', 'origin', self.config.default_branch], cwd=project_repo_path)
            
            self.logger.info(f"Successfully extracted project '{project.name}' to '{repo_name}'")
    
    def extract_common_component_to_repo(self, component: CommonComponent, repo_name: str, repo_url: str):
        """Extract a common component to its own repository."""
        component_repo_path = os.path.join(self.temp_dir, f"component_{component.name}")
        
        self.logger.info(f"Extracting common component '{component.name}' to repository '{repo_name}'")
        
        if not self.config.dry_run:
            # Clone the mirror repo
            self.run_git_command(['git', 'clone', self.source_repo_path, component_repo_path])
            
            # Validate component path exists
            target_path = os.path.join(component_repo_path, component.path)
            if not os.path.exists(target_path):
                self.logger.error(f"Common component path does not exist in repo: {component.path}")
                return
            
            # Use git filter-repo to extract only the component path
            self.run_git_command([
                'git', 'filter-repo',
                '--path', component.path,
                '--path-rename', f'{component.path}:',
                '--force'
            ], cwd=component_repo_path)
            
            # Remove remote origin
            self.run_git_command(['git', 'remote', 'remove', 'origin'], cwd=component_repo_path)
            
            # Add new remote
            self.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=component_repo_path)
            
            # Ensure default branch name
            self.run_git_command(['git', 'branch', '-M', self.config.default_branch], cwd=component_repo_path)
            # Push to the new repository
            self.run_git_command(['git', 'push', '-u', 'origin', self.config.default_branch], cwd=component_repo_path)
            
            self.logger.info(f"Successfully extracted common component '{component.name}' to '{repo_name}'")

    def extract_branch_to_repo(self, branch_name: str, repo_name: str, repo_url: str):
        """Extract a full branch to its own repository preserving history."""
        branch_repo_path = os.path.join(self.temp_dir, f"branch_{branch_name}")
        self.logger.info(f"Extracting branch '{branch_name}' to repository '{repo_name}'")
        if not self.config.dry_run:
            # Clone the mirror repo to working copy
            self.run_git_command(['git', 'clone', self.source_repo_path, branch_repo_path])
            
            # Validate branch exists
            exists = True
            try:
                self.run_git_command(['git', 'show-ref', '--verify', f'refs/heads/{branch_name}'], cwd=branch_repo_path)
            except Exception:
                try:
                    self.run_git_command(['git', 'show-ref', '--verify', f'refs/remotes/origin/{branch_name}'], cwd=branch_repo_path)
                except Exception:
                    exists = False
            if not exists:
                self.logger.error(f"Branch does not exist: {branch_name}")
                return
            # Checkout target branch (create local tracking)
            # Try both local and origin refs
            try:
                self.run_git_command(['git', 'checkout', branch_name], cwd=branch_repo_path)
            except Exception:
                self.run_git_command(['git', 'checkout', f'origin/{branch_name}'], cwd=branch_repo_path)
                self.run_git_command(['git', 'branch', branch_name, f'origin/{branch_name}'], cwd=branch_repo_path)
                self.run_git_command(['git', 'checkout', branch_name], cwd=branch_repo_path)
            # Rename to default branch if needed
            self.run_git_command(['git', 'branch', '-M', self.config.default_branch], cwd=branch_repo_path)
            # Remove and add new remote
            self.run_git_command(['git', 'remote', 'remove', 'origin'], cwd=branch_repo_path)
            self.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=branch_repo_path)
            # Push
            self.run_git_command(['git', 'push', '-u', 'origin', self.config.default_branch], cwd=branch_repo_path)
            self.logger.info(f"Successfully extracted branch '{branch_name}' to '{repo_name}'")
    
    def split_repositories(self):
        """Main method to split the monorepo into multiple repositories."""
        try:
            # Load configuration
            self.config = self.load_config()

            mode = (self.config.mode or 'auto').lower()
            if mode not in {'auto', 'project', 'branch'}:
                raise ValueError("MODE must be one of: auto, project, branch")

            if mode == 'auto':
                # Analyze monorepo structure
                projects, common_components = self.analyze_monorepo()

                if self.config.analyze_only:
                    self.logger.info("Analysis complete. Use --dry-run to see what would be created.")
                    return

                # Process projects
                for project_name, project in projects.items():
                    repo_name = self._sanitize_repo_name(self.config.repo_name_template_app.format(name=project.name))
                    description = f"{project.type.title()} application extracted from monorepo"
                    self.logger.info(f"Processing project: {project.name}")
                    repo_url = self.create_github_repo(repo_name, description)
                    if repo_url:
                        self.extract_project_to_repo(project, repo_name, repo_url)
                        self.logger.info(f"Repository URL: {repo_url}")
                    else:
                        self.logger.error(f"Failed to create repository for project: {project.name}")

                # Process common components
                for component_name, component in common_components.items():
                    repo_name = self._sanitize_repo_name(self.config.repo_name_template_lib.format(name=component.name))
                    description = "Common library component extracted from monorepo"
                    self.logger.info(f"Processing common component: {component.name}")
                    repo_url = self.create_github_repo(repo_name, description)
                    if repo_url:
                        self.extract_common_component_to_repo(component, repo_name, repo_url)
                        self.logger.info(f"Repository URL: {repo_url}")
                    else:
                        self.logger.error(f"Failed to create repository for common component: {component.name}")

            elif mode == 'project':
                # Project mode: use explicitly provided projects and optional common_path
                self.clone_source_repo()
                projects_list = self.config.manual_projects or []
                if not projects_list:
                    raise ValueError("PROJECTS (or MANUAL_PROJECTS) must be provided in project mode")
                for project_path in projects_list:
                    project_path = project_path.strip()
                    if not project_path:
                        continue
                    project_name = os.path.basename(project_path)
                    project = ProjectInfo(name=project_name, path=project_path, type='app')
                    repo_name = self._sanitize_repo_name(self.config.repo_name_template_app.format(name=project_name))
                    description = "Application extracted from monorepo"
                    self.logger.info(f"Processing project: {project.name}")
                    repo_url = self.create_github_repo(repo_name, description)
                    if repo_url:
                        self.extract_project_to_repo(project, repo_name, repo_url)
                        self.logger.info(f"Repository URL: {repo_url}")
                    else:
                        self.logger.error(f"Failed to create repository for project: {project.name}")
                # Common path
                if self.config.common_path:
                    comp_name = os.path.basename(self.config.common_path)
                    component = CommonComponent(name=comp_name, path=self.config.common_path)
                    repo_name = self._sanitize_repo_name(self.config.repo_name_template_lib.format(name=comp_name))
                    description = "Common library component extracted from monorepo"
                    self.logger.info(f"Processing common component: {component.name}")
                    repo_url = self.create_github_repo(repo_name, description)
                    if repo_url:
                        self.extract_common_component_to_repo(component, repo_name, repo_url)
                        self.logger.info(f"Repository URL: {repo_url}")
                    else:
                        self.logger.error(f"Failed to create repository for common component: {component.name}")

            elif mode == 'branch':
                # Branch mode: each branch to a repo
                self.clone_source_repo()
                branches = self.config.branches or []
                if not branches:
                    raise ValueError("BRANCHES must be provided in branch mode")
                for branch_name in branches:
                    name_clean = branch_name.strip()
                    if not name_clean:
                        continue
                    repo_name = self._sanitize_repo_name(self.config.repo_name_template_app.format(name=name_clean))
                    description = f"Repository extracted from branch {name_clean}"
                    self.logger.info(f"Processing branch: {name_clean}")
                    repo_url = self.create_github_repo(repo_name, description)
                    if repo_url:
                        self.extract_branch_to_repo(name_clean, repo_name, repo_url)
                        self.logger.info(f"Repository URL: {repo_url}")
                    else:
                        self.logger.error(f"Failed to create repository for branch: {name_clean}")

            # Summary
            self.logger.info("=" * 60)
            self.logger.info("🎉 REPOSITORY SPLITTING COMPLETED")
            self.logger.info("=" * 60)
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
    parser = argparse.ArgumentParser(description="Advanced GitHub Monorepo Splitter AI Agent")
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    parser.add_argument('--analyze-only', action='store_true', help='Only analyze the monorepo structure without splitting')
    # Universal CLI options
    parser.add_argument('--mode', choices=['auto', 'project', 'branch'], help='Splitting mode to use')
    parser.add_argument('--branches', help='Comma-separated list of branches for branch mode')
    parser.add_argument('--projects', help='Comma-separated list of project directories for project mode')
    parser.add_argument('--common-path', help='Path to common libraries folder for project mode')
    parser.add_argument('--private', dest='private_repos', action='store_true', help='Create repositories as private')
    parser.add_argument('--default-branch', help='Default branch name for created repositories (e.g., main, master)')
    parser.add_argument('--name-template-app', help='Template for app repos, e.g. "{name}-app"')
    parser.add_argument('--name-template-lib', help='Template for library repos, e.g. "{name}-lib"')
    args = parser.parse_args()
    
    try:
        # Create config
        config = RepoSplitterConfig(
            source_repo_url='',  # Will be loaded from .env
            org='',
            github_token='',
            dry_run=args.dry_run,
            analyze_only=args.analyze_only,
            mode=args.mode if args.mode else 'auto',
            branches=[b.strip() for b in args.branches.split(',')] if args.branches else None,
            manual_projects=[p.strip() for p in args.projects.split(',')] if args.projects else None,
            common_path=args.common_path if args.common_path else None,
            private_repos=bool(args.private_repos),
            default_branch=args.default_branch if args.default_branch else 'main',
            repo_name_template_app=args.name_template_app if args.name_template_app else '{name}-app',
            repo_name_template_lib=args.name_template_lib if args.name_template_lib else '{name}-lib'
        )
        
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
