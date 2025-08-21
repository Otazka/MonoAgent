"""Tests for dependency conflict detection functionality."""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock
from split_repo_agent import MonorepoAnalyzer, DependencyConflict, DependencyInfo, ProjectInfo


class TestDependencyConflictDetection:
    """Test dependency conflict detection functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = Mock()
        self.analyzer = MonorepoAnalyzer(self.temp_dir, self.logger)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_version_conflict_detection(self):
        """Test detection of version conflicts across projects."""
        # Create test projects with conflicting versions
        self.analyzer.projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=0),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='nodejs', files=[], size=0)
        }
        
        # Add conflicting dependency versions
        self.analyzer.dependency_details = {
            'frontend': [
                DependencyInfo(name='react', version='18.0.0', source='package.json', project_path='apps/frontend')
            ],
            'backend': [
                DependencyInfo(name='react', version='17.0.0', source='package.json', project_path='apps/backend')
            ]
        }
        
        # Run conflict detection
        self.analyzer._detect_version_conflicts()
        
        # Check that conflict was detected
        assert len(self.analyzer.conflicts) == 1
        conflict = self.analyzer.conflicts[0]
        assert conflict.conflict_type == 'version_mismatch'
        assert conflict.target_project == 'react'
        assert conflict.severity == 'high'
        assert 'react' in conflict.description

    def test_missing_dependency_detection(self):
        """Test detection of missing dependencies after splitting."""
        # Create test projects with internal dependencies
        self.analyzer.projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=0),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='nodejs', files=[], size=0),
            'shared': ProjectInfo(name='shared', path='shared', type='nodejs', files=[], size=0)
        }
        
        # Add internal dependencies
        self.analyzer.projects['frontend'].dependencies = ['shared']
        self.analyzer.projects['backend'].dependencies = ['shared']
        
        # Run conflict detection
        self.analyzer._detect_missing_dependencies()
        
        # Check that conflicts were detected
        assert len(self.analyzer.conflicts) == 2
        conflicts = {c.source_project: c for c in self.analyzer.conflicts}
        
        assert 'frontend' in conflicts
        assert conflicts['frontend'].conflict_type == 'missing_dependency'
        assert conflicts['frontend'].target_project == 'shared'
        assert conflicts['frontend'].severity == 'critical'
        
        assert 'backend' in conflicts
        assert conflicts['backend'].conflict_type == 'missing_dependency'
        assert conflicts['backend'].target_project == 'shared'
        assert conflicts['backend'].severity == 'critical'

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        # Create test projects with circular dependencies
        self.analyzer.projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=0),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='nodejs', files=[], size=0),
            'shared': ProjectInfo(name='shared', path='shared', type='nodejs', files=[], size=0)
        }
        
        # Add circular dependencies: frontend -> backend -> shared -> frontend
        self.analyzer.projects['frontend'].dependencies = ['backend']
        self.analyzer.projects['backend'].dependencies = ['shared']
        self.analyzer.projects['shared'].dependencies = ['frontend']
        
        # Run conflict detection
        self.analyzer._detect_circular_dependencies()
        
        # Check that circular dependency was detected
        assert len(self.analyzer.conflicts) == 1
        conflict = self.analyzer.conflicts[0]
        assert conflict.conflict_type == 'circular_dependency'
        assert conflict.severity == 'critical'
        assert 'circular dependency' in conflict.description.lower()

    def test_shared_dependency_detection(self):
        """Test detection of shared dependencies."""
        # Create test projects with shared dependencies
        self.analyzer.projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=0),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='nodejs', files=[], size=0)
        }
        
        # Add shared dependencies
        self.analyzer.dependency_details = {
            'frontend': [
                DependencyInfo(name='lodash', version='4.17.21', source='package.json', project_path='apps/frontend')
            ],
            'backend': [
                DependencyInfo(name='lodash', version='4.17.21', source='package.json', project_path='apps/backend')
            ]
        }
        
        # Run conflict detection
        self.analyzer._detect_shared_dependencies()
        
        # Check that shared dependency was detected
        assert len(self.analyzer.conflicts) == 1
        conflict = self.analyzer.conflicts[0]
        assert conflict.conflict_type == 'shared_dependency'
        assert conflict.target_project == 'lodash'
        assert conflict.severity == 'medium'
        assert 'lodash' in conflict.description

    def test_detailed_dependency_extraction_package_json(self):
        """Test extraction of detailed dependencies from package.json."""
        # Create test package.json
        package_json = {
            "dependencies": {
                "react": "^18.0.0",
                "lodash": "4.17.21"
            },
            "devDependencies": {
                "jest": "^27.0.0"
            },
            "peerDependencies": {
                "react-dom": "^18.0.0"
            }
        }
        
        package_path = os.path.join(self.temp_dir, 'package.json')
        with open(package_path, 'w') as f:
            json.dump(package_json, f)
        
        # Extract dependencies
        deps = self.analyzer._extract_detailed_dependencies('package.json')
        
        # Check results
        assert len(deps) == 4
        
        # Check regular dependencies
        react_dep = next(d for d in deps if d.name == 'react')
        assert react_dep.version == '^18.0.0'
        assert not react_dep.is_dev_dependency
        assert not react_dep.is_peer_dependency
        
        # Check dev dependencies
        jest_dep = next(d for d in deps if d.name == 'jest')
        assert jest_dep.version == '^27.0.0'
        assert jest_dep.is_dev_dependency
        assert not jest_dep.is_peer_dependency
        
        # Check peer dependencies
        react_dom_dep = next(d for d in deps if d.name == 'react-dom')
        assert react_dom_dep.version == '^18.0.0'
        assert not react_dom_dep.is_dev_dependency
        assert react_dom_dep.is_peer_dependency

    def test_detailed_dependency_extraction_requirements_txt(self):
        """Test extraction of detailed dependencies from requirements.txt."""
        # Create test requirements.txt
        requirements_content = """
        flask==2.0.1
        requests>=2.25.0
        pytest
        # This is a comment
        numpy<=1.21.0
        """
        
        requirements_path = os.path.join(self.temp_dir, 'requirements.txt')
        with open(requirements_path, 'w') as f:
            f.write(requirements_content)
        
        # Extract dependencies
        deps = self.analyzer._extract_detailed_dependencies('requirements.txt')
        
        # Check results
        assert len(deps) == 4
        
        # Check specific dependencies
        flask_dep = next(d for d in deps if d.name == 'flask')
        assert flask_dep.version == '2.0.1'
        
        requests_dep = next(d for d in deps if d.name == 'requests')
        assert requests_dep.version == '2.25.0'
        
        pytest_dep = next(d for d in deps if d.name == 'pytest')
        assert pytest_dep.version is None
        
        numpy_dep = next(d for d in deps if d.name == 'numpy')
        assert numpy_dep.version == '1.21.0'

    def test_no_conflicts_detected(self):
        """Test that no conflicts are detected when there are none."""
        # Create test projects without conflicts
        self.analyzer.projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=0),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='nodejs', files=[], size=0)
        }
        
        # Add non-conflicting dependencies
        self.analyzer.dependency_details = {
            'frontend': [
                DependencyInfo(name='react', version='18.0.0', source='package.json', project_path='apps/frontend')
            ],
            'backend': [
                DependencyInfo(name='flask', version='2.0.1', source='requirements.txt', project_path='apps/backend')
            ]
        }
        
        # Run all conflict detection methods
        self.analyzer._detect_version_conflicts()
        self.analyzer._detect_missing_dependencies()
        self.analyzer._detect_circular_dependencies()
        self.analyzer._detect_shared_dependencies()
        
        # Check that no conflicts were detected
        assert len(self.analyzer.conflicts) == 0

    def test_conflict_severity_levels(self):
        """Test that conflicts have appropriate severity levels."""
        # Create test projects
        self.analyzer.projects = {
            'frontend': ProjectInfo(name='frontend', path='apps/frontend', type='nodejs', files=[], size=0),
            'backend': ProjectInfo(name='backend', path='apps/backend', type='nodejs', files=[], size=0)
        }
        
        # Add different types of conflicts
        self.analyzer.projects['frontend'].dependencies = ['backend']  # Missing dependency
        self.analyzer.dependency_details = {
            'frontend': [
                DependencyInfo(name='lodash', version='4.17.21', source='package.json', project_path='apps/frontend')
            ],
            'backend': [
                DependencyInfo(name='lodash', version='4.17.21', source='package.json', project_path='apps/backend')
            ]
        }
        
        # Run conflict detection
        self.analyzer._detect_missing_dependencies()
        self.analyzer._detect_shared_dependencies()
        
        # Check severity levels
        conflicts = {c.conflict_type: c for c in self.analyzer.conflicts}
        
        assert conflicts['missing_dependency'].severity == 'critical'
        assert conflicts['shared_dependency'].severity == 'medium'
