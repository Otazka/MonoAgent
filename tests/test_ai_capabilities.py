"""Tests for AI capabilities and dependency graph visualization."""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch
from split_repo_agent import (
    DependencyGraphVisualizer, AIAnalyzer, AIRecommendation,
    ProjectInfo, CommonComponent, DependencyConflict
)


class TestDependencyGraphVisualizer:
    """Test dependency graph visualization functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = Mock()
        self.visualizer = DependencyGraphVisualizer(self.logger)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_graph_with_projects(self):
        """Test building graph with projects only."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15)
        }
        
        common_components = {}
        conflicts = []
        
        graph = self.visualizer.build_graph(projects, common_components, conflicts)
        
        assert len(graph.nodes) == 2
        assert 'frontend' in graph.nodes
        assert 'backend' in graph.nodes
        assert graph.nodes['frontend']['type'] == 'project'
        assert graph.nodes['backend']['type'] == 'project'

    def test_build_graph_with_components(self):
        """Test building graph with projects and components."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10)
        }
        
        common_components = {
            'utils': CommonComponent(name='utils', path='shared/utils', files=[], usage_count=2)
        }
        
        conflicts = []
        
        graph = self.visualizer.build_graph(projects, common_components, conflicts)
        
        assert len(graph.nodes) == 2
        assert 'frontend' in graph.nodes
        assert 'utils' in graph.nodes
        assert graph.nodes['frontend']['type'] == 'project'
        assert graph.nodes['utils']['type'] == 'component'

    def test_build_graph_with_dependencies(self):
        """Test building graph with dependency relationships."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15)
        }
        
        # Add dependencies
        projects['frontend'].dependencies = ['backend']
        
        common_components = {}
        conflicts = []
        
        graph = self.visualizer.build_graph(projects, common_components, conflicts)
        
        assert len(graph.edges) == 1
        assert ('frontend', 'backend') in graph.edges

    def test_build_graph_with_conflicts(self):
        """Test building graph with conflict edges."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15)
        }
        
        # Add dependencies
        projects['frontend'].dependencies = ['backend']
        
        common_components = {}
        conflicts = [
            DependencyConflict(
                source_project='frontend',
                target_project='backend',
                conflict_type='missing_dependency',
                description='Frontend depends on backend',
                severity='critical',
                resolution_suggestions=[]
            )
        ]
        
        graph = self.visualizer.build_graph(projects, common_components, conflicts)
        
        assert len(graph.edges) == 1
        edge_data = graph.get_edge_data('frontend', 'backend')
        assert edge_data['conflict'] is True
        assert edge_data['conflict_type'] == 'missing_dependency'

    def test_project_colors(self):
        """Test project color assignment."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15),
            'api': ProjectInfo(name='api', path='apps/api', type='java', files=[], size=20)
        }
        
        common_components = {}
        conflicts = []
        
        self.visualizer.build_graph(projects, common_components, conflicts)
        
        # Check that colors are assigned
        assert self.visualizer.project_colors['frontend'] == '#61DAFB'  # React blue
        assert self.visualizer.project_colors['backend'] == '#3776AB'   # Python blue
        assert self.visualizer.project_colors['api'] == '#ED8B00'       # Java orange

    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_generate_visualization(self, mock_close, mock_savefig):
        """Test visualization generation."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15)
        }
        
        common_components = {}
        conflicts = []
        
        self.visualizer.build_graph(projects, common_components, conflicts)
        
        output_path = self.visualizer.generate_visualization("test_graph.png")
        
        assert output_path == "test_graph.png"
        mock_savefig.assert_called_once()
        mock_close.assert_called_once()

    def test_generate_dot_file(self):
        """Test DOT file generation."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10)
        }
        
        common_components = {}
        conflicts = []
        
        self.visualizer.build_graph(projects, common_components, conflicts)
        
        output_path = self.visualizer.generate_dot_file("test_graph.dot")
        
        assert output_path == "test_graph.dot"
        assert os.path.exists("test_graph.dot")


class TestAIAnalyzer:
    """Test AI analyzer functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.logger = Mock()
        self.ai_analyzer = AIAnalyzer(self.logger)

    def test_analyze_architecture_technology_diversity(self):
        """Test architecture analysis for technology diversity."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15),
            'api': ProjectInfo(name='api', path='apps/api', type='java', files=[], size=20),
            'worker': ProjectInfo(name='worker', path='apps/worker', type='go', files=[], size=25)
        }
        
        common_components = {}
        conflicts = []
        
        recommendations = self.ai_analyzer.analyze_architecture(projects, common_components, conflicts)
        
        # Should recommend technology consolidation
        tech_consolidation = [r for r in recommendations if 'Technology Stack Consolidation' in r.title]
        assert len(tech_consolidation) == 1
        assert tech_consolidation[0].priority == 8

    def test_analyze_architecture_critical_conflicts(self):
        """Test architecture analysis for critical conflicts."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15)
        }
        
        common_components = {}
        conflicts = [
            DependencyConflict(
                source_project='frontend',
                target_project='backend',
                conflict_type='missing_dependency',
                description='Critical dependency issue',
                severity='critical',
                resolution_suggestions=[]
            )
        ]
        
        recommendations = self.ai_analyzer.analyze_architecture(projects, common_components, conflicts)
        
        # Should recommend conflict resolution
        conflict_resolution = [r for r in recommendations if 'Dependency Conflict Resolution' in r.title]
        assert len(conflict_resolution) == 1
        assert conflict_resolution[0].priority == 10
        assert conflict_resolution[0].impact == 'critical'

    def test_analyze_architecture_component_reuse(self):
        """Test architecture analysis for component reuse."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15),
            'api': ProjectInfo(name='api', path='apps/api', type='java', files=[], size=20),
            'worker': ProjectInfo(name='worker', path='apps/worker', type='go', files=[], size=25),
            'mobile': ProjectInfo(name='mobile', path='apps/mobile', type='flutter', files=[], size=30)
        }
        
        common_components = {
            'utils': CommonComponent(name='utils', path='shared/utils', files=[], usage_count=2)
        }
        
        conflicts = []
        
        recommendations = self.ai_analyzer.analyze_architecture(projects, common_components, conflicts)
        
        # Should recommend increasing component reuse (1 component < 5 projects * 0.3 = 1.5)
        component_reuse = [r for r in recommendations if 'Increase Component Reusability' in r.title]
        assert len(component_reuse) == 1
        assert component_reuse[0].priority == 6

    def test_analyze_performance_large_projects(self):
        """Test performance analysis for large projects."""
        projects = {
            'large_project': ProjectInfo(name='large_project', path='apps/large', type='nodejs', files=[], size=150)
        }
        
        recommendations = self.ai_analyzer.analyze_performance(projects)
        
        # Should recommend large project optimization
        large_project_opt = [r for r in recommendations if 'Large Project Optimization' in r.title]
        assert len(large_project_opt) == 1
        assert large_project_opt[0].priority == 7

    def test_analyze_security_many_projects(self):
        """Test security analysis for many projects."""
        projects = {
            f'project_{i}': ProjectInfo(name=f'project_{i}', path=f'apps/project_{i}', type='nodejs', files=[], size=10)
            for i in range(15)
        }
        
        recommendations = self.ai_analyzer.analyze_security(projects)
        
        # Should recommend access control
        access_control = [r for r in recommendations if 'Repository Access Control' in r.title]
        assert len(access_control) == 1
        assert access_control[0].priority == 8

    def test_generate_comprehensive_analysis(self):
        """Test comprehensive AI analysis generation."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15)
        }
        
        common_components = {
            'utils': CommonComponent(name='utils', path='shared/utils', files=[], usage_count=2)
        }
        
        conflicts = [
            DependencyConflict(
                source_project='frontend',
                target_project='backend',
                conflict_type='missing_dependency',
                description='Test conflict',
                severity='critical',
                resolution_suggestions=[]
            )
        ]
        
        analysis = self.ai_analyzer.generate_comprehensive_analysis(projects, common_components, conflicts)
        
        # Check structure
        assert 'timestamp' in analysis
        assert 'metrics' in analysis
        assert 'recommendations' in analysis
        assert 'summary' in analysis
        
        # Check metrics
        metrics = analysis['metrics']
        assert metrics['total_projects'] == 2
        assert metrics['total_components'] == 1
        assert metrics['total_conflicts'] == 1
        assert metrics['critical_conflicts'] == 1
        assert 'complexity_score' in metrics
        
        # Check summary
        summary = analysis['summary']
        assert 'readiness_score' in summary
        assert 'recommendation_count' in summary
        assert 'high_priority_count' in summary

    def test_complexity_score_calculation(self):
        """Test complexity score calculation."""
        projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=10),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='python', files=[], size=15)
        }
        
        common_components = {}
        conflicts = [
            DependencyConflict(
                source_project='frontend',
                target_project='backend',
                conflict_type='missing_dependency',
                description='Test conflict',
                severity='critical',
                resolution_suggestions=[]
            )
        ]
        
        score = self.ai_analyzer._calculate_complexity_score(projects, common_components, conflicts)
        
        # Score should be reasonable
        assert 0 <= score <= 100
        assert score > 0  # Should have some complexity

    def test_readiness_score_calculation(self):
        """Test readiness score calculation."""
        # No conflicts - should be 100
        conflicts = []
        score = self.ai_analyzer._calculate_readiness_score(conflicts)
        assert score == 100
        
        # With conflicts - should be lower
        conflicts = [
            DependencyConflict(
                source_project='frontend',
                target_project='backend',
                conflict_type='missing_dependency',
                description='Test conflict',
                severity='critical',
                resolution_suggestions=[]
            )
        ]
        
        score = self.ai_analyzer._calculate_readiness_score(conflicts)
        assert score < 100
        assert score >= 0


class TestAIRecommendation:
    """Test AI recommendation data structure."""

    def test_ai_recommendation_creation(self):
        """Test creating AI recommendation."""
        recommendation = AIRecommendation(
            category='architecture',
            title='Test Recommendation',
            description='Test description',
            impact='high',
            effort='medium',
            priority=8,
            implementation_steps=['Step 1', 'Step 2'],
            estimated_benefit='Improved performance'
        )
        
        assert recommendation.category == 'architecture'
        assert recommendation.title == 'Test Recommendation'
        assert recommendation.impact == 'high'
        assert recommendation.priority == 8
        assert len(recommendation.implementation_steps) == 2
        assert recommendation.estimated_benefit == 'Improved performance'
