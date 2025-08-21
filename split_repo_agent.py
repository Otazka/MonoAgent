#!/usr/bin/env python3
"""
Advanced GitHub Monorepo Splitter AI Agent

This AI agent intelligently analyzes and splits GitHub monorepos into multiple repositories,
handling complex scenarios:

1. Different apps on the same branch → Separate into different repos
2. Common/generic components → Separate into shared library repos  
3. Different apps on separate branches → Each app gets its own repo
4. Intelligent project structure detection and analysis
5. Dependency graph visualization and AI-powered recommendations

Usage:
    python split_repo_agent.py [--dry-run] [--analyze-only] [--visualize]

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
from datetime import datetime, timezone
from collections import defaultdict
import time

import requests
from dotenv import load_dotenv
from github import Github, GithubException
from tqdm import tqdm
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import graphviz
import copy


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
    force: bool = False  # Force proceed despite conflicts
    visualize: bool = False  # Generate dependency graph visualizations
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
    # GitHub API quota management
    rate_limit_min_remaining: int = 50
    abuse_retry_after_default: int = 60
    # Multi-provider support
    provider: str = "github"  # github | gitlab | bitbucket | azure
    gitlab_host: str = "https://gitlab.com"  # Override for self-hosted
    provider_username: Optional[str] = None   # Used for Bitbucket/Azure (PAT basic auth username)
    azure_project: Optional[str] = None       # Required for Azure DevOps repo creation


@dataclass
class DependencyConflict:
    """Represents a dependency conflict between projects."""
    source_project: str
    target_project: str
    conflict_type: str  # 'version_mismatch', 'missing_dependency', 'circular_dependency'
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class DependencyInfo:
    """Detailed dependency information."""
    name: str
    source: str  # 'package.json', 'requirements.txt', 'pom.xml', etc.
    project_path: str
    version: Optional[str] = None
    is_dev_dependency: bool = False
    is_peer_dependency: bool = False


@dataclass
class AIRecommendation:
    """AI-powered recommendation for monorepo optimization."""
    category: str  # 'architecture', 'performance', 'security', 'maintainability'
    title: str
    description: str
    impact: str  # 'high', 'medium', 'low'
    effort: str  # 'high', 'medium', 'low'
    priority: int  # 1-10, higher is more important
    implementation_steps: List[str] = field(default_factory=list)
    estimated_benefit: str = ""


class DependencyGraphVisualizer:
    """AI-powered dependency graph visualization and analysis."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.graph = nx.DiGraph()
        self.project_colors = {}
        self.component_colors = {}
        self.conflict_edges = []
        
    def build_graph(self, projects: Dict[str, ProjectInfo], 
                   common_components: Dict[str, CommonComponent],
                   conflicts: List[DependencyConflict]) -> nx.DiGraph:
        """Build a NetworkX graph from projects, components, and conflicts."""
        self.logger.info("🔄 Building dependency graph...")
        
        # Add project nodes
        for project_name, project in projects.items():
            self.graph.add_node(project_name, 
                              type='project', 
                              language=project.type,
                              size=project.size,
                              path=project.path)
            self.project_colors[project_name] = self._get_project_color(project.type)
        
        # Add component nodes
        for component_name, component in common_components.items():
            self.graph.add_node(component_name,
                              type='component',
                              language='shared',
                              size=len(component.files),
                              path=component.path)
            self.component_colors[component_name] = '#FFD700'  # Gold for components
        
        # Add dependency edges
        for project_name, project in projects.items():
            for dep in project.dependencies:
                if dep in projects or dep in common_components:
                    self.graph.add_edge(project_name, dep, 
                                      type='dependency',
                                      weight=1)
        
        # Mark conflict edges
        for conflict in conflicts:
            if conflict.conflict_type in ['missing_dependency', 'circular_dependency']:
                self.conflict_edges.append((conflict.source_project, conflict.target_project))
                if self.graph.has_edge(conflict.source_project, conflict.target_project):
                    self.graph[conflict.source_project][conflict.target_project]['conflict'] = True
                    self.graph[conflict.source_project][conflict.target_project]['conflict_type'] = conflict.conflict_type
        
        return self.graph
    
    def _get_project_color(self, project_type: str) -> str:
        """Get color for project type."""
        colors = {
            'nodejs': '#61DAFB',    # React blue
            'python': '#3776AB',    # Python blue
            'java': '#ED8B00',      # Java orange
            'go': '#00ADD8',        # Go blue
            'rust': '#DEA584',      # Rust orange
            'php': '#777BB4',       # PHP purple
            'ruby': '#CC342D',      # Ruby red
            'app': '#4CAF50',       # Green for generic apps
            'shared': '#FFD700'     # Gold for shared
        }
        return colors.get(project_type, '#9E9E9E')  # Gray default
    
    def generate_visualization(self, output_path: str = "dependency_graph.png") -> str:
        """Generate a beautiful dependency graph visualization."""
        self.logger.info("🎨 Generating dependency graph visualization...")
        
        # Set up the plot
        plt.figure(figsize=(16, 12))
        plt.style.use('default')
        
        # Use spring layout for better positioning
        pos = nx.spring_layout(self.graph, k=3, iterations=50, seed=42)
        
        # Draw nodes
        self._draw_nodes(pos)
        
        # Draw edges
        self._draw_edges(pos)
        
        # Add legend
        self._add_legend()
        
        # Add title and labels
        plt.title("Monorepo Dependency Graph", fontsize=20, fontweight='bold', pad=20)
        plt.axis('off')
        
        # Save the visualization
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        self.logger.info(f"📊 Dependency graph saved to: {output_path}")
        return output_path
    
    def _draw_nodes(self, pos):
        """Draw nodes with different styles for projects and components."""
        # Draw project nodes
        project_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'project']
        component_nodes = [n for n, d in self.graph.nodes(data=True) if d.get('type') == 'component']
        
        # Project nodes (larger, colored)
        nx.draw_networkx_nodes(self.graph, pos, 
                             nodelist=project_nodes,
                             node_color=[self.project_colors.get(n, '#9E9E9E') for n in project_nodes],
                             node_size=2000,
                             alpha=0.8,
                             edgecolors='black',
                             linewidths=2)
        
        # Component nodes (smaller, gold)
        nx.draw_networkx_nodes(self.graph, pos,
                             nodelist=component_nodes,
                             node_color=[self.component_colors.get(n, '#FFD700') for n in component_nodes],
                             node_size=1500,
                             alpha=0.8,
                             edgecolors='black',
                             linewidths=2)
        
        # Add node labels
        nx.draw_networkx_labels(self.graph, pos, font_size=10, font_weight='bold')
    
    def _draw_edges(self, pos):
        """Draw edges with different styles for normal and conflict dependencies."""
        # Normal edges
        normal_edges = [(u, v) for u, v in self.graph.edges() 
                       if not self.graph[u][v].get('conflict', False)]
        nx.draw_networkx_edges(self.graph, pos,
                             edgelist=normal_edges,
                             edge_color='#666666',
                             arrows=True,
                             arrowsize=20,
                             arrowstyle='->',
                             width=1.5,
                             alpha=0.6)
        
        # Conflict edges (red, thicker)
        conflict_edges = [(u, v) for u, v in self.graph.edges() 
                         if self.graph[u][v].get('conflict', False)]
        nx.draw_networkx_edges(self.graph, pos,
                             edgelist=conflict_edges,
                             edge_color='#FF4444',
                             arrows=True,
                             arrowsize=25,
                             arrowstyle='->',
                             width=3,
                             alpha=0.8)
    
    def _add_legend(self):
        """Add a comprehensive legend to the visualization."""
        legend_elements = []
        
        # Project type colors
        project_types = {
            'Node.js': '#61DAFB',
            'Python': '#3776AB',
            'Java': '#ED8B00',
            'Go': '#00ADD8',
            'Components': '#FFD700'
        }
        
        for label, color in project_types.items():
            legend_elements.append(mpatches.Patch(color=color, label=label))
        
        # Edge types
        legend_elements.append(plt.Line2D([0], [0], color='#666666', lw=2, label='Normal Dependency'))
        legend_elements.append(plt.Line2D([0], [0], color='#FF4444', lw=3, label='Conflict Dependency'))
        
        plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1), fontsize=12)
    
    def generate_dot_file(self, output_path: str = "dependency_graph.dot") -> str:
        """Generate a Graphviz DOT file for advanced visualization."""
        self.logger.info("🔄 Generating Graphviz DOT file...")
        
        dot = graphviz.Digraph(comment='Monorepo Dependency Graph')
        dot.attr(rankdir='TB', size='16,12', dpi='300')
        
        # Add nodes
        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'project':
                color = self.project_colors.get(node, '#9E9E9E')
                shape = 'box'
                style = 'filled'
            else:
                color = self.component_colors.get(node, '#FFD700')
                shape = 'ellipse'
                style = 'filled'
            
            dot.node(node, node, 
                    fillcolor=color, 
                    style=style, 
                    shape=shape,
                    fontsize='12',
                    fontweight='bold')
        
        # Add edges
        for u, v, data in self.graph.edges(data=True):
            if data.get('conflict', False):
                color = 'red'
                penwidth = '3'
            else:
                color = 'black'
                penwidth = '1'
            
            dot.edge(u, v, color=color, penwidth=penwidth)
        
        # Save DOT file
        dot.save(output_path)
        self.logger.info(f"📊 DOT file saved to: {output_path}")
        return output_path
    
    def generate_svg(self, output_path: str = "dependency_graph.svg") -> str:
        """Generate SVG visualization from DOT file."""
        try:
            dot_file = self.generate_dot_file()
            graphviz.render('dot', 'svg', dot_file, outfile=output_path)
            self.logger.info(f"📊 SVG visualization saved to: {output_path}")
            return output_path
        except Exception as e:
            self.logger.warning(f"Could not generate SVG: {e}")
            return ""


class AIAnalyzer:
    """AI-powered analysis and recommendations for monorepo optimization."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.recommendations = []
    
    def analyze_architecture(self, projects: Dict[str, ProjectInfo], 
                           common_components: Dict[str, CommonComponent],
                           conflicts: List[DependencyConflict]) -> List[AIRecommendation]:
        """Generate AI-powered architectural recommendations."""
        self.logger.info("🤖 Generating AI-powered architectural recommendations...")
        
        recommendations = []
        
        # Analyze project distribution
        project_types = defaultdict(int)
        for project in projects.values():
            project_types[project.type] += 1
        
        # Recommendation: Standardize technology stack
        if len(project_types) > 3:
            recommendations.append(AIRecommendation(
                category='architecture',
                title='Technology Stack Consolidation',
                description=f'Consider consolidating from {len(project_types)} different technologies to reduce complexity',
                impact='high',
                effort='medium',
                priority=8,
                implementation_steps=[
                    'Audit current technology usage across projects',
                    'Identify most suitable technology for each domain',
                    'Create migration plan for non-standard technologies',
                    'Implement shared libraries for common functionality'
                ],
                estimated_benefit='Reduced maintenance overhead and improved developer productivity'
            ))
        
        # Analyze dependency conflicts
        critical_conflicts = [c for c in conflicts if c.severity == 'critical']
        if critical_conflicts:
            recommendations.append(AIRecommendation(
                category='architecture',
                title='Dependency Conflict Resolution',
                description=f'Resolve {len(critical_conflicts)} critical dependency conflicts before splitting',
                impact='critical',
                effort='high',
                priority=10,
                implementation_steps=[
                    'Review each critical conflict in detail',
                    'Implement shared dependency management strategy',
                    'Create common component libraries',
                    'Update project dependencies to use shared versions'
                ],
                estimated_benefit='Prevent build failures and runtime issues in separated repositories'
            ))
        
        # Analyze component sharing
        if len(common_components) < len(projects) * 0.3:
            recommendations.append(AIRecommendation(
                category='architecture',
                title='Increase Component Reusability',
                description='Extract more common components to improve code reuse',
                impact='medium',
                effort='medium',
                priority=6,
                implementation_steps=[
                    'Identify duplicate code across projects',
                    'Extract common utilities and components',
                    'Create shared library structure',
                    'Update projects to use shared components'
                ],
                estimated_benefit='Reduced code duplication and improved maintainability'
            ))
        
        return recommendations
    
    def analyze_performance(self, projects: Dict[str, ProjectInfo]) -> List[AIRecommendation]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze project sizes
        large_projects = [p for p in projects.values() if p.size > 100]
        if large_projects:
            recommendations.append(AIRecommendation(
                category='performance',
                title='Large Project Optimization',
                description=f'Consider splitting {len(large_projects)} large projects for better performance',
                impact='medium',
                effort='high',
                priority=7,
                implementation_steps=[
                    'Analyze large project dependencies',
                    'Identify logical boundaries for splitting',
                    'Create separate repositories for large components',
                    'Update build and deployment processes'
                ],
                estimated_benefit='Improved build times and deployment efficiency'
            ))
        
        return recommendations
    
    def analyze_security(self, projects: Dict[str, ProjectInfo]) -> List[AIRecommendation]:
        """Generate security recommendations."""
        recommendations = []
        
        # Check for potential security issues
        if len(projects) > 10:
            recommendations.append(AIRecommendation(
                category='security',
                title='Repository Access Control',
                description='Implement granular access controls for separated repositories',
                impact='high',
                effort='medium',
                priority=8,
                implementation_steps=[
                    'Define access control policies for each repository',
                    'Set up team-based permissions',
                    'Implement branch protection rules',
                    'Configure security scanning for each repository'
                ],
                estimated_benefit='Improved security through principle of least privilege'
            ))
        
        return recommendations
    
    def generate_comprehensive_analysis(self, projects: Dict[str, ProjectInfo],
                                      common_components: Dict[str, CommonComponent],
                                      conflicts: List[DependencyConflict]) -> Dict:
        """Generate comprehensive AI analysis report."""
        self.logger.info("🤖 Generating comprehensive AI analysis...")
        
        # Get recommendations from all categories
        arch_recs = self.analyze_architecture(projects, common_components, conflicts)
        perf_recs = self.analyze_performance(projects)
        sec_recs = self.analyze_security(projects)
        
        all_recommendations = arch_recs + perf_recs + sec_recs
        
        # Sort by priority
        all_recommendations.sort(key=lambda x: x.priority, reverse=True)
        
        # Calculate metrics
        total_projects = len(projects)
        total_components = len(common_components)
        total_conflicts = len(conflicts)
        critical_conflicts = len([c for c in conflicts if c.severity == 'critical'])
        
        # Generate complexity score
        complexity_score = self._calculate_complexity_score(projects, common_components, conflicts)
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {
                'total_projects': total_projects,
                'total_components': total_components,
                'total_conflicts': total_conflicts,
                'critical_conflicts': critical_conflicts,
                'complexity_score': complexity_score
            },
            'recommendations': [
                {
                    'category': rec.category,
                    'title': rec.title,
                    'description': rec.description,
                    'impact': rec.impact,
                    'effort': rec.effort,
                    'priority': rec.priority,
                    'implementation_steps': rec.implementation_steps,
                    'estimated_benefit': rec.estimated_benefit
                }
                for rec in all_recommendations
            ],
            'summary': {
                'readiness_score': self._calculate_readiness_score(conflicts),
                'recommendation_count': len(all_recommendations),
                'high_priority_count': len([r for r in all_recommendations if r.priority >= 8])
            }
        }
        
        return analysis
    
    def _calculate_complexity_score(self, projects: Dict[str, ProjectInfo],
                                  common_components: Dict[str, CommonComponent],
                                  conflicts: List[DependencyConflict]) -> float:
        """Calculate complexity score (0-100, higher is more complex)."""
        score = 0
        
        # Project count factor
        score += min(len(projects) * 2, 30)
        
        # Conflict factor
        score += len(conflicts) * 3
        
        # Critical conflict factor
        critical_conflicts = len([c for c in conflicts if c.severity == 'critical'])
        score += critical_conflicts * 5
        
        # Technology diversity factor
        project_types = set(p.type for p in projects.values())
        score += len(project_types) * 2
        
        return min(score, 100)
    
    def _calculate_readiness_score(self, conflicts: List[DependencyConflict]) -> float:
        """Calculate readiness score for splitting (0-100, higher is more ready)."""
        if not conflicts:
            return 100
        
        # Deduct points for conflicts
        score = 100
        score -= len(conflicts) * 5
        score -= len([c for c in conflicts if c.severity == 'critical']) * 10
        
        return max(score, 0)


class MonorepoAnalyzer:
    """AI-powered analyzer for monorepo structure detection."""
    
    def __init__(self, repo_path: str, logger: logging.Logger):
        self.repo_path = repo_path
        self.logger = logger
        self.projects: Dict[str, ProjectInfo] = {}
        self.common_components: Dict[str, CommonComponent] = {}
        self.file_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.dependency_details: Dict[str, List[DependencyInfo]] = {}
        self.conflicts: List[DependencyConflict] = []
        
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
        
        # First, count total files for progress bar
        total_files = 0
        for root, dirs, filenames in os.walk(self.repo_path):
            if '.git' in dirs:
                dirs.remove('.git')
            total_files += len(filenames)
        
        # Now collect files with progress bar
        with tqdm(total=total_files, desc="📁 Scanning files", unit="file") as pbar:
            for root, dirs, filenames in os.walk(self.repo_path):
                # Skip .git directory
                if '.git' in dirs:
                    dirs.remove('.git')
                
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, self.repo_path)
                    files.append(rel_path)
                    pbar.update(1)
        
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
        with tqdm(total=len(all_files), desc="🔍 Grouping files by directory", unit="file") as pbar:
            for file_path in all_files:
                dir_path = os.path.dirname(file_path)
                dir_files[dir_path].append(file_path)
                pbar.update(1)
        
        # Detect projects based on indicators
        with tqdm(total=len(dir_files), desc="🎯 Detecting projects", unit="dir") as pbar:
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
                pbar.update(1)
        
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
        
        with tqdm(total=len(all_files), desc="🏗️  Analyzing directory structure", unit="file") as pbar:
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
                pbar.update(1)
    
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
        
        with tqdm(total=len(all_files), desc="🔧 Detecting common components", unit="file") as pbar:
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
                pbar.update(1)
    
    def _analyze_dependencies(self):
        """Analyze dependencies between projects and components."""
        self.logger.info("🔗 Analyzing dependencies between projects...")
        
        total_files = sum(len([f for f in project.files if f.endswith(('.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go'))]) 
                         for project in self.projects.values())
        
        with tqdm(total=total_files, desc="🔗 Analyzing dependencies", unit="file") as pbar:
            for project_name, project in self.projects.items():
                self.dependency_details[project_name] = []
                for file_path in project.files:
                    if file_path.endswith(('.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go')):
                        dependencies = self._extract_dependencies(file_path)
                        project.dependencies.extend(dependencies)
                        pbar.update(1)
                
                # Remove duplicates
                project.dependencies = list(set(project.dependencies))
        
        # Detect dependency conflicts
        self._detect_dependency_conflicts()
    
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

    def _extract_detailed_dependencies(self, file_path: str) -> List[DependencyInfo]:
        """Extract detailed dependency information from configuration files."""
        dependencies = []
        full_path = os.path.join(self.repo_path, file_path)
        
        try:
            if file_path.endswith('package.json'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Extract dependencies
                for dep_type, deps in data.items():
                    if dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                        for dep_name, dep_version in deps.items():
                            dependencies.append(DependencyInfo(
                                name=dep_name,
                                source='package.json',
                                project_path=os.path.dirname(file_path),
                                version=dep_version,
                                is_dev_dependency=(dep_type == 'devDependencies'),
                                is_peer_dependency=(dep_type == 'peerDependencies')
                            ))
                            
            elif file_path.endswith('requirements.txt'):
                with open(full_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            # Parse requirements.txt format
                            if '==' in line:
                                name, version = line.split('==', 1)
                            elif '>=' in line:
                                name, version = line.split('>=', 1)
                            elif '<=' in line:
                                name, version = line.split('<=', 1)
                            else:
                                name, version = line, None
                                
                            dependencies.append(DependencyInfo(
                                name=name.strip(),
                                source='requirements.txt',
                                project_path=os.path.dirname(file_path),
                                version=version.strip() if version else None
                            ))
                            
            elif file_path.endswith('pom.xml'):
                # Basic XML parsing for Maven dependencies
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Extract groupId and artifactId
                artifact_pattern = r'<artifactId>([^<]+)</artifactId>'
                group_pattern = r'<groupId>([^<]+)</groupId>'
                version_pattern = r'<version>([^<]+)</version>'
                
                artifacts = re.findall(artifact_pattern, content)
                groups = re.findall(group_pattern, content)
                versions = re.findall(version_pattern, content)
                
                for i, artifact in enumerate(artifacts):
                    group = groups[i] if i < len(groups) else 'unknown'
                    version = versions[i] if i < len(versions) else None
                    
                    dependencies.append(DependencyInfo(
                        name=f"{group}:{artifact}",
                        source='pom.xml',
                        project_path=os.path.dirname(file_path),
                        version=version
                    ))
                    
        except Exception as e:
            self.logger.debug(f"Error reading dependency file {file_path}: {e}")
            
        return dependencies

    def _detect_dependency_conflicts(self):
        """Detect dependency conflicts between projects."""
        self.logger.info("⚠️  Detecting dependency conflicts...")
        
        # Extract detailed dependencies from configuration files
        for project_name, project in self.projects.items():
            for file_path in project.files:
                if file_path.endswith(('package.json', 'requirements.txt', 'pom.xml', 'build.gradle')):
                    deps = self._extract_detailed_dependencies(file_path)
                    self.dependency_details[project_name].extend(deps)
        
        # Detect version conflicts
        self._detect_version_conflicts()
        
        # Detect missing dependencies
        self._detect_missing_dependencies()
        
        # Detect circular dependencies
        self._detect_circular_dependencies()
        
        # Detect shared dependencies
        self._detect_shared_dependencies()

    def _detect_version_conflicts(self):
        """Detect version conflicts for the same dependency across projects."""
        dependency_versions = defaultdict(dict)
        
        # Collect all dependency versions
        for project_name, deps in self.dependency_details.items():
            for dep in deps:
                if dep.version:
                    dependency_versions[dep.name][project_name] = dep.version
        
        # Check for version conflicts
        for dep_name, versions in dependency_versions.items():
            if len(set(versions.values())) > 1:
                # Version conflict detected
                conflict = DependencyConflict(
                    source_project="multiple",
                    target_project=dep_name,
                    conflict_type="version_mismatch",
                    description=f"Version conflict for '{dep_name}': {dict(versions)}",
                    severity="high",
                    resolution_suggestions=[
                        f"Standardize '{dep_name}' version across all projects",
                        f"Move '{dep_name}' to a shared dependency management system",
                        f"Consider creating a shared library for '{dep_name}'"
                    ]
                )
                self.conflicts.append(conflict)

    def _detect_missing_dependencies(self):
        """Detect dependencies that will be missing after splitting."""
        # Check for internal project dependencies
        for project_name, project in self.projects.items():
            for dep in project.dependencies:
                # Check if dependency is another project in the monorepo
                if dep in self.projects and dep != project_name:
                    conflict = DependencyConflict(
                        source_project=project_name,
                        target_project=dep,
                        conflict_type="missing_dependency",
                        description=f"Project '{project_name}' depends on project '{dep}' which will be separated",
                        severity="critical",
                        resolution_suggestions=[
                            f"Move shared code from '{dep}' to a common component",
                            f"Create a shared library for '{dep}'",
                            f"Update '{project_name}' to use external dependency for '{dep}'",
                            f"Keep '{project_name}' and '{dep}' in the same repository"
                        ]
                    )
                    self.conflicts.append(conflict)

    def _detect_circular_dependencies(self):
        """Detect circular dependencies between projects."""
        # Build dependency graph
        graph = defaultdict(set)
        for project_name, project in self.projects.items():
            for dep in project.dependencies:
                if dep in self.projects:
                    graph[project_name].add(dep)
        
        # Detect cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        # Check for cycles
        for project_name in self.projects:
            if project_name not in visited:
                if has_cycle(project_name):
                    # Find the cycle
                    cycle = self._find_cycle(graph, project_name)
                    conflict = DependencyConflict(
                        source_project="circular",
                        target_project="->".join(cycle),
                        conflict_type="circular_dependency",
                        description=f"Circular dependency detected: {' -> '.join(cycle)}",
                        severity="critical",
                        resolution_suggestions=[
                            "Extract shared functionality to a common component",
                            "Refactor to break the circular dependency",
                            "Use dependency injection or interfaces",
                            "Consider merging the circularly dependent projects"
                        ]
                    )
                    self.conflicts.append(conflict)

    def _find_cycle(self, graph, start_node):
        """Find a cycle in the dependency graph."""
        visited = set()
        path = []
        
        def dfs(node):
            if node in path:
                cycle_start = path.index(node)
                return path[cycle_start:] + [node]
            
            if node in visited:
                return None
                
            visited.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                result = dfs(neighbor)
                if result:
                    return result
            
            path.pop()
            return None
        
        return dfs(start_node) or []

    def _detect_shared_dependencies(self):
        """Detect dependencies that are shared across multiple projects."""
        shared_deps = defaultdict(set)
        
        # Find shared dependencies
        for project_name, deps in self.dependency_details.items():
            for dep in deps:
                shared_deps[dep.name].add(project_name)
        
        # Report shared dependencies
        for dep_name, projects in shared_deps.items():
            if len(projects) > 1:
                conflict = DependencyConflict(
                    source_project="shared",
                    target_project=dep_name,
                    conflict_type="shared_dependency",
                    description=f"'{dep_name}' is used by {len(projects)} projects: {', '.join(projects)}",
                    severity="medium",
                    resolution_suggestions=[
                        f"Consider creating a shared library for '{dep_name}'",
                        f"Move '{dep_name}' to a common component",
                        f"Use a monorepo package manager (Lerna, Nx, Rush) for '{dep_name}'"
                    ]
                )
                self.conflicts.append(conflict)
    
    def _generate_analysis_report(self):
        """Generate a comprehensive analysis report."""
        self.logger.info("📊 Generating analysis report...")
        
        # Initialize AI analyzer and visualizer
        ai_analyzer = AIAnalyzer(self.logger)
        visualizer = DependencyGraphVisualizer(self.logger)
        
        # Build dependency graph
        graph = visualizer.build_graph(self.projects, self.common_components, self.conflicts)
        
        # Generate AI analysis
        ai_analysis = ai_analyzer.generate_comprehensive_analysis(
            self.projects, self.common_components, self.conflicts
        )
        
        # Generate visualizations
        visualization_paths = {}
        try:
            visualization_paths['png'] = visualizer.generate_visualization("dependency_graph.png")
            visualization_paths['dot'] = visualizer.generate_dot_file("dependency_graph.dot")
            visualization_paths['svg'] = visualizer.generate_svg("dependency_graph.svg")
        except Exception as e:
            self.logger.warning(f"Could not generate visualizations: {e}")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_projects': len(self.projects),
            'total_common_components': len(self.common_components),
            'total_conflicts': len(self.conflicts),
            'projects': {},
            'common_components': {},
            'dependency_conflicts': [],
            'recommendations': [],
            'ai_analysis': ai_analysis,
            'visualizations': visualization_paths
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
        
        # Add dependency conflicts
        for conflict in self.conflicts:
            report['dependency_conflicts'].append({
                'source_project': conflict.source_project,
                'target_project': conflict.target_project,
                'conflict_type': conflict.conflict_type,
                'description': conflict.description,
                'severity': conflict.severity,
                'resolution_suggestions': conflict.resolution_suggestions
            })
        
        # Generate recommendations
        recommendations = []
        
        if len(self.projects) > 1:
            recommendations.append(f"Split {len(self.projects)} detected projects into separate repositories")
        
        if self.common_components:
            recommendations.append(f"Extract {len(self.common_components)} common components into shared libraries")
        
        if len(self.projects) > 5:
            recommendations.append("Consider creating a shared library for common utilities")
        
        # Add conflict-based recommendations
        critical_conflicts = [c for c in self.conflicts if c.severity == 'critical']
        high_conflicts = [c for c in self.conflicts if c.severity == 'high']
        
        if critical_conflicts:
            recommendations.append(f"⚠️  Resolve {len(critical_conflicts)} critical dependency conflicts before splitting")
        
        if high_conflicts:
            recommendations.append(f"⚠️  Address {len(high_conflicts)} high-severity dependency conflicts")
        
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
        
        # Print dependency conflicts
        if self.conflicts:
            self.logger.info(f"⚠️  Detected {len(self.conflicts)} dependency conflicts:")
            for conflict in self.conflicts:
                severity_emoji = {
                    'low': '🟢',
                    'medium': '🟡', 
                    'high': '🟠',
                    'critical': '🔴'
                }.get(conflict.severity, '⚪')
                
                self.logger.info(f"  {severity_emoji} {conflict.conflict_type.upper()}: {conflict.description}")
                for suggestion in conflict.resolution_suggestions[:2]:  # Show first 2 suggestions
                    self.logger.info(f"    💡 {suggestion}")
        else:
            self.logger.info("✅ No dependency conflicts detected")
        
        # Print AI analysis
        if 'ai_analysis' in report:
            ai_analysis = report['ai_analysis']
            self.logger.info("🤖 AI-POWERED ANALYSIS")
            self.logger.info("=" * 60)
            
            # Print metrics
            metrics = ai_analysis['metrics']
            self.logger.info(f"📊 Complexity Score: {metrics['complexity_score']}/100")
            self.logger.info(f"📊 Readiness Score: {ai_analysis['summary']['readiness_score']}/100")
            
            # Print high-priority recommendations
            high_priority_recs = [r for r in ai_analysis['recommendations'] if r['priority'] >= 8]
            if high_priority_recs:
                self.logger.info(f"🚨 {len(high_priority_recs)} High-Priority Recommendations:")
                for rec in high_priority_recs[:3]:  # Show top 3
                    impact_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(rec['impact'], '⚪')
                    self.logger.info(f"  {impact_emoji} [{rec['priority']}] {rec['title']}")
                    self.logger.info(f"    📝 {rec['description']}")
                    self.logger.info(f"    💡 Benefit: {rec['estimated_benefit']}")
            
            # Print visualization info
            if report.get('visualizations'):
                self.logger.info("📊 Visualizations Generated:")
                for format_name, path in report['visualizations'].items():
                    if path:
                        self.logger.info(f"  • {format_name.upper()}: {path}")
        
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

    # ------------------
    # Preflight checks
    # ------------------
    def preflight_checks(self) -> bool:
        """Validate environment, binaries, and provider token reachability."""
        ok = True
        # git
        if shutil.which('git') is None:
            self.logger.error("git not found in PATH. Install git and retry.")
            ok = False
        # git-filter-repo
        if shutil.which('git-filter-repo') is None:
            self.logger.warning("git-filter-repo not found. Install for path/history filtering.")
        # graphviz/dot (optional)
        if self.config.visualize and shutil.which('dot') is None:
            self.logger.warning("Graphviz 'dot' not found. Visualizations (PNG/SVG) will be skipped.")

        # SOURCE_REPO_URL reachability
        try:
            self.run_git_command(['git', 'ls-remote', '--heads', self.config.source_repo_url], check=False)
        except Exception:
            self.logger.warning("Could not verify SOURCE_REPO_URL reachability. Ensure the URL and SSH agent are configured.")

        # Provider token minimal check
        provider = (self.config.provider or 'github').lower()
        try:
            if provider == 'github':
                self._rate_limit_guard()
                _ = self.github.get_user().login
            elif provider == 'gitlab':
                import requests
                base = (self.config.gitlab_host or 'https://gitlab.com').rstrip('/')
                resp = requests.get(f"{base}/api/v4/user", headers={"PRIVATE-TOKEN": self.config.github_token}, timeout=10)
                if resp.status_code != 200:
                    self.logger.error(f"GitLab token check failed: {resp.status_code} {resp.text}")
                    ok = False
            elif provider == 'bitbucket':
                import requests
                user = self.config.provider_username or self.config.org
                auth = (user, self.config.github_token)
                resp = requests.get("https://api.bitbucket.org/2.0/user", auth=auth, timeout=10)
                if resp.status_code != 200:
                    self.logger.error(f"Bitbucket token check failed: {resp.status_code} {resp.text}")
                    ok = False
            elif provider == 'azure':
                import requests, base64
                org = self.config.org
                project = self.config.azure_project
                if not project:
                    self.logger.error("azure_project must be set for Azure DevOps provider")
                    ok = False
                token = base64.b64encode(f":{self.config.github_token}".encode()).decode()
                headers = {"Authorization": f"Basic {token}"}
                url = f"https://dev.azure.com/{org}/_apis/projects?api-version=7.1-preview.4"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    self.logger.error(f"Azure DevOps PAT check failed: {resp.status_code} {resp.text}")
                    ok = False
        except Exception as e:
            self.logger.error(f"Provider preflight check failed: {e}")
            ok = False

        if ok:
            self.logger.info("✅ Preflight checks passed")
        else:
            self.logger.error("❌ Preflight checks failed. See messages above.")
        return ok
    
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
        
        # Validate required fields (actionable messages)
        if not config.source_repo_url:
            raise ValueError(
                "SOURCE_REPO_URL is required. Set in .env or pass via CLI. Example: git@github.com:org/monorepo.git"
            )
        if not config.org:
            raise ValueError(
                "ORG is required. Set your GitHub org or username in .env (ORG=your-org)."
            )
        if not config.github_token:
            raise ValueError(
                "GITHUB_TOKEN is required. Create a token with repo scope and export in .env (GITHUB_TOKEN=...)."
            )
        
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

    # ----------------------------
    # package.json migration logic
    # ----------------------------
    @staticmethod
    def _transform_package_json(original: Dict, *, repo_name: str, repo_url: str, is_library: bool) -> Dict:
        """Pure function: given original package.json as dict, return migrated copy.

        - Sets name, version (if missing), and repository fields
        - Ensures private=false for apps; libraries left as configured
        - Adds basic scripts if missing
        - Converts workspaces-specific fields to standard standalone form
        """
        pkg = copy.deepcopy(original) if isinstance(original, dict) else {}

        # Name
        pkg['name'] = pkg.get('name') or repo_name

        # Version
        if 'version' not in pkg:
            pkg['version'] = '1.0.0'

        # Repository metadata
        repo_meta = {
            'type': 'git',
            'url': repo_url
        }
        pkg['repository'] = pkg.get('repository') or repo_meta
        pkg['homepage'] = pkg.get('homepage') or repo_url.replace('.git', '')

        # Private handling
        if not is_library:
            # Applications typically shouldn't be private in a new public repo unless configured
            # Respect explicit private=true if present; otherwise default to False
            if 'private' not in pkg:
                pkg['private'] = False

        # Basic scripts fallbacks
        scripts = pkg.get('scripts') or {}
        if 'test' not in scripts:
            scripts['test'] = 'echo "No tests specified" && exit 0'
        if 'build' not in scripts:
            # Pick a reasonable default based on presence of common toolchains
            if 'tsconfig.json' in pkg.get('files', []) or pkg.get('types'):
                scripts['build'] = 'tsc -p .'
            else:
                scripts['build'] = 'echo "No build step"'
        pkg['scripts'] = scripts

        # Workspaces clean-up for standalone
        if 'workspaces' in pkg:
            pkg.pop('workspaces', None)

        # Engines are optional – keep as is
        return pkg

    def _migrate_node_project(self, package_json_path: str, *, repo_name: str, repo_url: str, is_library: bool) -> None:
        """If package.json exists at path, migrate it for standalone use.

        Safe to call even if the file does not exist; silently returns.
        """
        if not os.path.exists(package_json_path):
            return
        try:
            with open(package_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.logger.debug(f"Failed reading package.json: {e}")
            return

        migrated = self._transform_package_json(data, repo_name=repo_name, repo_url=repo_url, is_library=is_library)

        try:
            with open(package_json_path, 'w', encoding='utf-8') as f:
                json.dump(migrated, f, indent=2, ensure_ascii=False)
            self.logger.info(f"🧩 Migrated package.json at {package_json_path}")
        except Exception as e:
            self.logger.debug(f"Failed writing migrated package.json: {e}")
    
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

    # -----------------------
    # GitHub Rate Limit Guard
    # -----------------------
    def _rate_limit_guard(self) -> None:
        if not self.github:
            return
        try:
            rl = self.github.get_rate_limit().core
            remaining = getattr(rl, 'remaining', None)
            reset = getattr(rl, 'reset', None)
            if remaining is not None and reset is not None and remaining <= self.config.rate_limit_min_remaining:
                now = datetime.now(timezone.utc)
                wait_seconds = max((reset - now).total_seconds(), 0) + 1
                self.logger.warning(f"⏳ GitHub rate limit low (remaining={remaining}). Waiting {int(wait_seconds)}s until reset...")
                time.sleep(wait_seconds)
        except Exception as e:
            self.logger.debug(f"Rate limit check failed: {e}")

    def _handle_github_exception_backoff(self, exc: GithubException) -> None:
        retry_after = None
        try:
            headers = getattr(exc, 'headers', None) or getattr(exc, 'data', {})
            if isinstance(headers, dict):
                val = headers.get('Retry-After') or headers.get('retry-after')
                if val:
                    retry_after = int(val)
        except Exception:
            pass

        if retry_after is None:
            try:
                rl = self.github.get_rate_limit().core
                now = datetime.now(timezone.utc)
                retry_after = max(int((rl.reset - now).total_seconds()) + 1, self.config.abuse_retry_after_default)
            except Exception:
                retry_after = self.config.abuse_retry_after_default

        self.logger.warning(f"🛑 GitHub API throttled: waiting {retry_after}s before retrying...")
        time.sleep(retry_after)
    
    def clone_source_repo(self) -> str:
        """Clone the source repository to a temporary directory."""
        self.temp_dir = tempfile.mkdtemp(prefix="repo_splitter_")
        self.source_repo_path = os.path.join(self.temp_dir, "source_repo")
        
        self.logger.info(f"Cloning source repository: {self.config.source_repo_url}")
        self.logger.info(f"Temporary directory: {self.temp_dir}")
        
        # Show progress for cloning
        with tqdm(desc="📥 Cloning repository", unit="B", unit_scale=True, unit_divisor=1024) as pbar:
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
        
        # Check for critical conflicts
        critical_conflicts = [c for c in self.analyzer.conflicts if c.severity == 'critical']
        if critical_conflicts and not self.config.dry_run:
            self.logger.warning(f"⚠️  Found {len(critical_conflicts)} critical dependency conflicts!")
            self.logger.warning("Consider resolving these conflicts before proceeding with the split.")
            
            # Ask for confirmation in non-dry-run mode
            if not self.config.force:
                self.logger.error("❌ Aborting due to critical dependency conflicts. Use --force to proceed anyway.")
                raise ValueError(f"Critical dependency conflicts detected: {len(critical_conflicts)} conflicts")
        
        return projects, common_components
    
    def _create_repo_provider_agnostic(self, repo_name: str, description: str = "") -> Optional[str]:
        """Create a new repository across supported providers and return clone URL."""
        provider = (self.config.provider or 'github').lower()
        if provider == 'github':
            return self._create_repo_github(repo_name, description)
        elif provider == 'gitlab':
            return self._create_repo_gitlab(repo_name, description)
        elif provider == 'bitbucket':
            return self._create_repo_bitbucket(repo_name, description)
        elif provider == 'azure':
            return self._create_repo_azure(repo_name, description)
        else:
            self.logger.error(f"Unsupported provider: {provider}")
            return None

    def create_github_repo(self, repo_name: str, description: str = "") -> Optional[str]:
        """Backward compatibility shim: still called in code paths; now delegates to provider-agnostic."""
        return self._create_repo_provider_agnostic(repo_name, description)

    # ----------------
    # Provider: GitHub
    # ----------------
    def _create_repo_github(self, repo_name: str, description: str = "") -> Optional[str]:
        """Create repo in GitHub and return clone URL."""
        # Sanitize name early for consistent logs
        repo_name = self._sanitize_repo_name(repo_name)
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would create repo: {repo_name}")
            return f"https://github.com/{self.config.org}/{repo_name}.git"
        
        with tqdm(desc=f"📝 Creating {repo_name}", unit="attempt", total=3) as pbar:
            last_exc: Optional[Exception] = None
            for attempt in range(1, 4):
                try:
                    self._rate_limit_guard()
                    # Check if repo already exists
                    try:
                        existing_repo = self.github.get_repo(f"{self.config.org}/{repo_name}")
                        self.logger.warning(f"Repository {repo_name} already exists, skipping creation")
                        pbar.update(1)
                        return existing_repo.clone_url
                    except GithubException:
                        pass
                    
                    # Try as organization first; fallback to user
                    try:
                        self._rate_limit_guard()
                        org = self.github.get_organization(self.config.org)
                        repo = org.create_repo(
                            name=repo_name,
                            description=description,
                            private=self.config.private_repos,
                            auto_init=False
                        )
                    except GithubException:
                        self._rate_limit_guard()
                        user = self.github.get_user()
                        repo = user.create_repo(
                            name=repo_name,
                            description=description,
                            private=self.config.private_repos,
                            auto_init=False
                        )
                    
                    self.logger.info(f"Created repository: {repo_name}")
                    self.created_repos.append(repo_name)
                    pbar.update(1)
                    return repo.clone_url
                except GithubException as e:
                    last_exc = e
                    self.logger.warning(f"GitHub API error creating {repo_name} (attempt {attempt}/3): {e}")
                    if getattr(e, 'status', None) == 403 or 'rate limit' in str(e).lower() or 'abuse' in str(e).lower():
                        self._handle_github_exception_backoff(e)
                    else:
                        time.sleep(min(2 ** attempt, 8))
                    pbar.update(1)
        
        self.logger.error(f"Failed to create repository {repo_name}: {last_exc}")
        return None

    # ---------------
    # Provider: GitLab
    # ---------------
    def _create_repo_gitlab(self, repo_name: str, description: str = "") -> Optional[str]:
        """Create repo in GitLab and return clone URL."""
        try:
            import requests
        except Exception:
            self.logger.error("Requests library not available for GitLab operations")
            return None
        base = (self.config.gitlab_host or 'https://gitlab.com').rstrip('/')
        token = self.config.github_token  # reuse token env for simplicity
        headers = {"PRIVATE-TOKEN": token}
        data = {
            "name": self._sanitize_repo_name(repo_name),
            "path": self._sanitize_repo_name(repo_name),
            "visibility": "private" if self.config.private_repos else "public",
            "description": description,
        }
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would create GitLab project: {data['name']}")
            return f"{base}/{self.config.org}/{data['path']}.git"
        try:
            self._rate_limit_guard()
            resp = requests.post(f"{base}/api/v4/projects", headers=headers, data=data, timeout=30)
            if resp.status_code in (200, 201):
                info = resp.json()
                clone_url = info.get('ssh_url_to_repo') or info.get('http_url_to_repo')
                self.logger.info(f"Created GitLab project: {data['name']}")
                self.created_repos.append(data['name'])
                return clone_url
            elif resp.status_code == 409:
                self.logger.warning("GitLab project already exists; continuing")
                return f"{base}/{self.config.org}/{data['path']}.git"
            else:
                self.logger.error(f"GitLab API error {resp.status_code}: {resp.text}")
        except Exception as e:
            self.logger.error(f"GitLab project creation failed: {e}")
        return None

    # -----------------
    # Provider: Bitbucket
    # -----------------
    def _create_repo_bitbucket(self, repo_name: str, description: str = "") -> Optional[str]:
        """Create repo in Bitbucket Cloud and return clone URL."""
        try:
            import requests
        except Exception:
            self.logger.error("Requests library not available for Bitbucket operations")
            return None
        base = "https://api.bitbucket.org/2.0"
        user = self.config.provider_username or self.config.org
        token = self.config.github_token
        auth = (user, token)
        data = {
            "scm": "git",
            "is_private": bool(self.config.private_repos),
            "description": description,
        }
        name = self._sanitize_repo_name(repo_name)
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would create Bitbucket repo: {name}")
            return f"git@bitbucket.org:{user}/{name}.git"
        try:
            self._rate_limit_guard()
            resp = requests.post(f"{base}/repositories/{user}/{name}", auth=auth, json=data, timeout=30)
            if resp.status_code in (200, 201):
                info = resp.json()
                links = info.get('links', {})
                clone = links.get('clone', [])
                ssh = next((c['href'] for c in clone if c.get('name') == 'ssh'), None)
                https = next((c['href'] for c in clone if c.get('name') == 'https'), None)
                clone_url = ssh or https
                self.logger.info(f"Created Bitbucket repo: {name}")
                self.created_repos.append(name)
                return clone_url
            elif resp.status_code == 400 and 'already exists' in resp.text.lower():
                self.logger.warning("Bitbucket repo already exists; continuing")
                return f"git@bitbucket.org:{user}/{name}.git"
            else:
                self.logger.error(f"Bitbucket API error {resp.status_code}: {resp.text}")
        except Exception as e:
            self.logger.error(f"Bitbucket repo creation failed: {e}")
        return None

    # -----------------
    # Provider: Azure DevOps
    # -----------------
    def _create_repo_azure(self, repo_name: str, description: str = "") -> Optional[str]:
        """Create repo in Azure DevOps and return clone URL.

        Requires:
          - ORG as Azure DevOps organization
          - azure_project in config
          - provider_username and github_token as PAT credentials
        """
        try:
            import requests
            import base64
        except Exception:
            self.logger.error("Requests library not available for Azure operations")
            return None
        org = self.config.org
        project = self.config.azure_project
        if not project:
            self.logger.error("azure_project is required for Azure DevOps provider")
            return None
        user = self.config.provider_username or ""
        pat = self.config.github_token
        token = base64.b64encode(f":{pat}".encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json"
        }
        name = self._sanitize_repo_name(repo_name)
        payload = {"name": name}
        if self.config.dry_run:
            self.logger.info(f"[DRY RUN] Would create Azure DevOps repo: {name}")
            return f"https://dev.azure.com/{org}/{project}/_git/{name}"
        try:
            self._rate_limit_guard()
            url = f"https://dev.azure.com/{org}/{project}/_apis/git/repositories?api-version=7.1-preview.1"
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code in (200, 201):
                info = resp.json()
                clone_url = next((l['href'] for l in info.get('remoteUrl', []) if l.get('name') == 'ssh'), None)
                clone_url = clone_url or info.get('sshUrl') or info.get('remoteUrl')
                self.logger.info(f"Created Azure DevOps repo: {name}")
                self.created_repos.append(name)
                return clone_url
            elif resp.status_code == 409:
                self.logger.warning("Azure repo already exists; continuing")
                return f"https://dev.azure.com/{org}/{project}/_git/{name}"
            else:
                self.logger.error(f"Azure API error {resp.status_code}: {resp.text}")
        except Exception as e:
            self.logger.error(f"Azure DevOps repo creation failed: {e}")
        return None
    
    def extract_project_to_repo(self, project: ProjectInfo, repo_name: str, repo_url: str):
        """Extract a project to its own repository."""
        project_repo_path = os.path.join(self.temp_dir, f"project_{project.name}")
        
        self.logger.info(f"Extracting project '{project.name}' to repository '{repo_name}'")
        
        if not self.config.dry_run:
            with tqdm(total=7, desc=f"📦 Extracting {project.name}", unit="step") as pbar:
                # Clone the mirror repo
                self.run_git_command(['git', 'clone', self.source_repo_path, project_repo_path])
                pbar.update(1)
                
                # Validate project path exists
                target_path = os.path.join(project_repo_path, project.path)
                if not os.path.exists(target_path):
                    self.logger.error(f"Project path does not exist in repo: {project.path}")
                    return
                pbar.update(1)
                
                # Use git filter-repo to extract only the project path
                self.run_git_command([
                    'git', 'filter-repo',
                    '--path', project.path,
                    '--path-rename', f'{project.path}:',
                    '--force'
                ], cwd=project_repo_path)
                pbar.update(1)
                
                # Attempt to migrate package.json for standalone usage
                try:
                    self._migrate_node_project(os.path.join(project_repo_path, 'package.json'),
                                               repo_name=repo_name,
                                               repo_url=repo_url,
                                               is_library=False)
                except Exception as e:
                    self.logger.debug(f"package.json migration skipped/failed: {e}")

                # Remove remote origin
                self.run_git_command(['git', 'remote', 'remove', 'origin'], cwd=project_repo_path)
                pbar.update(1)
                
                # Add new remote
                self.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=project_repo_path)
                pbar.update(1)
                
                # Ensure default branch name
                self.run_git_command(['git', 'branch', '-M', self.config.default_branch], cwd=project_repo_path)
                pbar.update(1)
                
                # Push to the new repository
                self.run_git_command(['git', 'push', '-u', 'origin', self.config.default_branch], cwd=project_repo_path)
                pbar.update(1)
            
            self.logger.info(f"Successfully extracted project '{project.name}' to '{repo_name}'")
    
    def extract_common_component_to_repo(self, component: CommonComponent, repo_name: str, repo_url: str):
        """Extract a common component to its own repository."""
        component_repo_path = os.path.join(self.temp_dir, f"component_{component.name}")
        
        self.logger.info(f"Extracting common component '{component.name}' to repository '{repo_name}'")
        
        if not self.config.dry_run:
            with tqdm(total=7, desc=f"🔧 Extracting {component.name}", unit="step") as pbar:
                # Clone the mirror repo
                self.run_git_command(['git', 'clone', self.source_repo_path, component_repo_path])
                pbar.update(1)
                
                # Validate component path exists
                target_path = os.path.join(component_repo_path, component.path)
                if not os.path.exists(target_path):
                    self.logger.error(f"Common component path does not exist in repo: {component.path}")
                    return
                pbar.update(1)
                
                # Use git filter-repo to extract only the component path
                self.run_git_command([
                    'git', 'filter-repo',
                    '--path', component.path,
                    '--path-rename', f'{component.path}:',
                    '--force'
                ], cwd=component_repo_path)
                pbar.update(1)
                
                # Attempt to migrate package.json for standalone usage
                try:
                    self._migrate_node_project(os.path.join(component_repo_path, 'package.json'),
                                               repo_name=repo_name,
                                               repo_url=repo_url,
                                               is_library=True)
                except Exception as e:
                    self.logger.debug(f"package.json migration skipped/failed: {e}")

                # Remove remote origin
                self.run_git_command(['git', 'remote', 'remove', 'origin'], cwd=component_repo_path)
                pbar.update(1)
                
                # Add new remote
                self.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=component_repo_path)
                pbar.update(1)
                
                # Ensure default branch name
                self.run_git_command(['git', 'branch', '-M', self.config.default_branch], cwd=component_repo_path)
                pbar.update(1)
                
                # Push to the new repository
                self.run_git_command(['git', 'push', '-u', 'origin', self.config.default_branch], cwd=component_repo_path)
                pbar.update(1)
            
            self.logger.info(f"Successfully extracted common component '{component.name}' to '{repo_name}'")

    def extract_branch_to_repo(self, branch_name: str, repo_name: str, repo_url: str):
        """Extract a full branch to its own repository preserving history."""
        branch_repo_path = os.path.join(self.temp_dir, f"branch_{branch_name}")
        self.logger.info(f"Extracting branch '{branch_name}' to repository '{repo_name}'")
        if not self.config.dry_run:
            with tqdm(total=8, desc=f"🌿 Extracting {branch_name}", unit="step") as pbar:
                # Clone the mirror repo to working copy
                self.run_git_command(['git', 'clone', self.source_repo_path, branch_repo_path])
                pbar.update(1)
                
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
                pbar.update(1)
                
                # Checkout target branch (create local tracking)
                # Try both local and origin refs
                try:
                    self.run_git_command(['git', 'checkout', branch_name], cwd=branch_repo_path)
                except Exception:
                    self.run_git_command(['git', 'checkout', f'origin/{branch_name}'], cwd=branch_repo_path)
                    self.run_git_command(['git', 'branch', branch_name, f'origin/{branch_name}'], cwd=branch_repo_path)
                    self.run_git_command(['git', 'checkout', branch_name], cwd=branch_repo_path)
                pbar.update(1)
                
                # Rename to default branch if needed
                self.run_git_command(['git', 'branch', '-M', self.config.default_branch], cwd=branch_repo_path)
                pbar.update(1)
                
                # Remove and add new remote
                self.run_git_command(['git', 'remote', 'remove', 'origin'], cwd=branch_repo_path)
                pbar.update(1)
                
                self.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=branch_repo_path)
                pbar.update(1)
                
                # Push
                self.run_git_command(['git', 'push', '-u', 'origin', self.config.default_branch], cwd=branch_repo_path)
                pbar.update(1)
                
                pbar.update(1)  # Final step
                
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

                # Process projects with progress bar
                total_items = len(projects) + len(common_components)
                with tqdm(total=total_items, desc="🚀 Creating repositories", unit="repo") as pbar:
                    # Process projects
                    for project_name, project in projects.items():
                        repo_name = self._sanitize_repo_name(self.config.repo_name_template_app.format(name=project.name))
                        description = f"{project.type.title()} application extracted from monorepo"
                        self.logger.info(f"Processing project: {project.name}")
                        repo_url = self._create_repo_provider_agnostic(repo_name, description)
                        if repo_url:
                            self.extract_project_to_repo(project, repo_name, repo_url)
                            self.logger.info(f"Repository URL: {repo_url}")
                        else:
                            self.logger.error(f"Failed to create repository for project: {project.name}")
                        pbar.update(1)

                    # Process common components
                    for component_name, component in common_components.items():
                        repo_name = self._sanitize_repo_name(self.config.repo_name_template_lib.format(name=component.name))
                        description = "Common library component extracted from monorepo"
                        self.logger.info(f"Processing common component: {component.name}")
                        repo_url = self._create_repo_provider_agnostic(repo_name, description)
                        if repo_url:
                            self.extract_common_component_to_repo(component, repo_name, repo_url)
                            self.logger.info(f"Repository URL: {repo_url}")
                        else:
                            self.logger.error(f"Failed to create repository for common component: {component.name}")
                        pbar.update(1)

            elif mode == 'project':
                # Project mode: use explicitly provided projects and optional common_path
                self.clone_source_repo()
                projects_list = self.config.manual_projects or []
                if not projects_list:
                    raise ValueError("PROJECTS (or MANUAL_PROJECTS) must be provided in project mode")
                
                total_items = len(projects_list) + (1 if self.config.common_path else 0)
                with tqdm(total=total_items, desc="🚀 Creating project repositories", unit="repo") as pbar:
                    for project_path in projects_list:
                        project_path = project_path.strip()
                        if not project_path:
                            continue
                        project_name = os.path.basename(project_path)
                        project = ProjectInfo(name=project_name, path=project_path, type='app')
                        repo_name = self._sanitize_repo_name(self.config.repo_name_template_app.format(name=project_name))
                        description = "Application extracted from monorepo"
                        self.logger.info(f"Processing project: {project.name}")
                        repo_url = self._create_repo_provider_agnostic(repo_name, description)
                        if repo_url:
                            self.extract_project_to_repo(project, repo_name, repo_url)
                            self.logger.info(f"Repository URL: {repo_url}")
                        else:
                            self.logger.error(f"Failed to create repository for project: {project.name}")
                        pbar.update(1)
                    
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
                        pbar.update(1)

            elif mode == 'branch':
                # Branch mode: each branch to a repo
                self.clone_source_repo()
                branches = self.config.branches or []
                if not branches:
                    raise ValueError("BRANCHES must be provided in branch mode")
                
                with tqdm(total=len(branches), desc="🌿 Creating branch repositories", unit="branch") as pbar:
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
                        pbar.update(1)

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
    parser.add_argument('--force', action='store_true', help='Force proceed despite dependency conflicts')
    parser.add_argument('--visualize', action='store_true', help='Generate dependency graph visualizations')
    parser.add_argument('--preflight', action='store_true', help='Run preflight checks and exit')
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
            force=args.force,
            visualize=args.visualize,
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
            if args.preflight:
                ok = splitter.preflight_checks()
                sys.exit(0 if ok else 1)
            splitter.split_repositories()
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
