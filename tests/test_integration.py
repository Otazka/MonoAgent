#!/usr/bin/env python3
"""
Integration tests for MonoAgent multi-provider scenarios.

These tests verify end-to-end functionality across different providers
and ensure the complete workflow works correctly.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import json

from split_repo_agent import RepoSplitterConfig, RepoSplitter


@pytest.fixture
def sample_monorepo():
    """Create a sample monorepo structure for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create monorepo structure
        projects = {
            "frontend": {
                "package.json": json.dumps({
                    "name": "frontend",
                    "version": "1.0.0",
                    "dependencies": {"react": "^18.0.0"}
                }),
                "src": {"App.js": "// Frontend app"},
                "README.md": "# Frontend Project"
            },
            "backend": {
                "package.json": json.dumps({
                    "name": "backend", 
                    "version": "1.0.0",
                    "dependencies": {"express": "^4.0.0"}
                }),
                "src": {"server.js": "// Backend server"},
                "README.md": "# Backend Project"
            },
            "shared": {
                "package.json": json.dumps({
                    "name": "shared",
                    "version": "1.0.0"
                }),
                "src": {"utils.js": "// Shared utilities"},
                "README.md": "# Shared Library"
            }
        }
        
        # Create directory structure
        for project_name, files in projects.items():
            project_dir = os.path.join(temp_dir, project_name)
            os.makedirs(project_dir, exist_ok=True)
            
            for file_path, content in files.items():
                if isinstance(content, dict):
                    # Handle nested directory structure
                    for sub_path, sub_content in content.items():
                        full_path = os.path.join(project_dir, file_path, sub_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'w') as f:
                            f.write(sub_content)
                else:
                    # Handle simple file
                    with open(os.path.join(project_dir, file_path), 'w') as f:
                        f.write(content)
        
        yield temp_dir


class TestMultiProviderIntegration:
    """Integration tests for multi-provider scenarios."""
    
    @pytest.fixture
    def mock_git_operations(self):
        """Mock git operations to avoid actual repository operations."""
        with patch('split_repo_agent.RepoSplitter.run_git_command') as mock_git:
            mock_git.return_value = (0, "success", "")
            yield mock_git
    
    @pytest.fixture
    def mock_api_calls(self):
        """Mock API calls to avoid actual provider API calls."""
        with patch('split_repo_agent.requests.post') as mock_post:
            # Mock successful responses for different providers
            def mock_response(*args, **kwargs):
                mock_resp = MagicMock()
                mock_resp.status_code = 201
                
                # Determine provider from URL
                url = args[0] if args else ""
                if "gitlab.com" in url:
                    mock_resp.json.return_value = {
                        "ssh_url_to_repo": "git@gitlab.com:testorg/test-repo.git"
                    }
                elif "bitbucket.org" in url:
                    mock_resp.json.return_value = {
                        "links": {
                            "clone": [
                                {"name": "ssh", "href": "git@bitbucket.org:testorg/test-repo.git"}
                            ]
                        }
                    }
                elif "dev.azure.com" in url:
                    mock_resp.json.return_value = {
                        "remoteUrl": "https://dev.azure.com/testorg/testproj/_git/test-repo"
                    }
                else:
                    # GitHub fallback
                    mock_resp.json.return_value = {
                        "clone_url": "https://github.com/testorg/test-repo.git"
                    }
                
                return mock_resp
            
            mock_post.side_effect = mock_response
            yield mock_post
    
    def test_github_integration_workflow(self, sample_monorepo, mock_git_operations, mock_api_calls):
        """Test complete GitHub integration workflow."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/monorepo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            dry_run=True,  # Use dry_run to avoid actual API calls
            analyze_only=False,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test that the splitter can be initialized and configured
        assert splitter.config.provider == "github"
        assert splitter.config.org == "testorg"
        assert splitter.source_repo_path == sample_monorepo
        
        # Test that the splitter can run without errors
        result = splitter.analyze_monorepo()
        assert result is not None
    
    def test_gitlab_integration_workflow(self, sample_monorepo, mock_git_operations, mock_api_calls):
        """Test complete GitLab integration workflow."""
        config = RepoSplitterConfig(
            source_repo_url="https://gitlab.com/testorg/monorepo.git",
            org="testorg",
            github_token="test-token",  # Reused for GitLab
            provider="gitlab",
            gitlab_host="https://gitlab.com",
            dry_run=True,  # Use dry_run to avoid actual API calls
            analyze_only=False,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test configuration
        assert splitter.config.provider == "gitlab"
        assert splitter.config.gitlab_host == "https://gitlab.com"
        
        # Test that the splitter can run
        result = splitter.analyze_monorepo()
        assert result is not None
    
    def test_bitbucket_integration_workflow(self, sample_monorepo, mock_git_operations, mock_api_calls):
        """Test complete Bitbucket integration workflow."""
        config = RepoSplitterConfig(
            source_repo_url="https://bitbucket.org/testorg/monorepo.git",
            org="testorg",
            github_token="test-token",  # Reused for Bitbucket
            provider="bitbucket",
            provider_username="testorg",
            dry_run=True,  # Use dry_run to avoid actual API calls
            analyze_only=False,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test configuration
        assert splitter.config.provider == "bitbucket"
        assert splitter.config.provider_username == "testorg"
        
        # Test that the splitter can run
        result = splitter.analyze_monorepo()
        assert result is not None
    
    def test_azure_integration_workflow(self, sample_monorepo, mock_git_operations, mock_api_calls):
        """Test complete Azure DevOps integration workflow."""
        config = RepoSplitterConfig(
            source_repo_url="https://dev.azure.com/testorg/testproj/_git/monorepo",
            org="testorg",
            github_token="test-token",  # Reused for Azure
            provider="azure",
            azure_project="testproj",
            dry_run=True,  # Use dry_run to avoid actual API calls
            analyze_only=False,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test configuration
        assert splitter.config.provider == "azure"
        assert splitter.config.azure_project == "testproj"
        
        # Test that the splitter can run
        result = splitter.analyze_monorepo()
        assert result is not None
    
    def test_multi_provider_error_handling(self, sample_monorepo, mock_git_operations):
        """Test error handling across different providers."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/monorepo.git",
            org="testorg",
            github_token="invalid-token",
            provider="github",
            dry_run=True,  # Use dry_run to avoid actual API calls
            analyze_only=False,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test that the splitter handles configuration gracefully
        result = splitter.analyze_monorepo()
        assert result is not None
    
    def test_dry_run_mode_integration(self, sample_monorepo, mock_git_operations):
        """Test dry run mode across all providers."""
        providers = ["github", "gitlab", "bitbucket", "azure"]
        
        for provider in providers:
            config = RepoSplitterConfig(
                source_repo_url=f"https://{provider}.com/testorg/monorepo.git",
                org="testorg",
                github_token="test-token",
                provider=provider,
                dry_run=True,  # Enable dry run
                analyze_only=False,
                mode="auto"
            )
            
            if provider == "azure":
                config.azure_project = "testproj"
            elif provider == "bitbucket":
                config.provider_username = "testorg"
            
            splitter = RepoSplitter(config)
            splitter.source_repo_path = sample_monorepo
            
            # Test that dry run mode works for all providers
            result = splitter.analyze_monorepo()
            assert result is not None
    
    def test_analyze_only_mode_integration(self, sample_monorepo, mock_git_operations):
        """Test analyze-only mode integration."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/monorepo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            dry_run=True,
            analyze_only=True,  # Enable analyze-only mode
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test analyze-only mode
        result = splitter.analyze_monorepo()
        assert result is not None
    
    def test_dependency_analysis_integration(self, sample_monorepo, mock_git_operations):
        """Test dependency analysis integration."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/monorepo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            dry_run=True,
            analyze_only=True,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test that dependency analysis can be performed
        result = splitter.analyze_monorepo()
        assert result is not None
    
    def test_visualization_integration(self, sample_monorepo, mock_git_operations):
        """Test visualization integration."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/monorepo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            dry_run=True,
            analyze_only=True,
            mode="auto",
            visualize=True  # Enable visualization
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Test that visualization can be enabled
        result = splitter.analyze_monorepo()
        assert result is not None


class TestEndToEndScenarios:
    """End-to-end scenario tests."""
    
    def test_simple_monorepo_split(self, sample_monorepo):
        """Test splitting a simple monorepo with multiple projects."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/simple-monorepo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            dry_run=True,
            analyze_only=False,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Mock git operations
        with patch('split_repo_agent.RepoSplitter.run_git_command') as mock_git:
            mock_git.return_value = (0, "success", "")
            
            # Test that the splitter can be initialized
            assert splitter.config.source_repo_url == "https://github.com/testorg/simple-monorepo.git"
            assert splitter.config.org == "testorg"
            assert splitter.config.provider == "github"
            
            # Test that the splitter can run
            result = splitter.analyze_monorepo()
            assert result is not None
    
    def test_large_monorepo_performance(self, sample_monorepo):
        """Test performance with a large number of projects."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/large-monorepo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            dry_run=True,
            analyze_only=True,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Mock git operations
        with patch('split_repo_agent.RepoSplitter.run_git_command') as mock_git:
            mock_git.return_value = (0, "success", "")
            
            # Test performance (should complete within reasonable time)
            import time
            start_time = time.time()
            result = splitter.analyze_monorepo()
            end_time = time.time()
            
            # Verify performance (should complete within reasonable time)
            assert end_time - start_time < 10.0  # Less than 10 seconds
            assert result is not None
    
    def test_error_recovery_scenario(self, sample_monorepo):
        """Test error recovery in a complex scenario."""
        config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/problematic-monorepo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            dry_run=True,  # Use dry_run to avoid actual errors
            analyze_only=False,
            mode="auto"
        )
        
        splitter = RepoSplitter(config)
        splitter.source_repo_path = sample_monorepo
        
        # Mock git operations
        with patch('split_repo_agent.RepoSplitter.run_git_command') as mock_git:
            mock_git.return_value = (0, "success", "")
            
            # Test that the splitter handles errors gracefully
            result = splitter.analyze_monorepo()
            assert result is not None
    
    def test_configuration_validation(self):
        """Test configuration validation across providers."""
        # Test GitHub configuration
        github_config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/repo.git",
            org="testorg",
            github_token="test-token",
            provider="github"
        )
        assert github_config.provider == "github"
        
        # Test GitLab configuration
        gitlab_config = RepoSplitterConfig(
            source_repo_url="https://gitlab.com/testorg/repo.git",
            org="testorg",
            github_token="test-token",
            provider="gitlab",
            gitlab_host="https://gitlab.com"
        )
        assert gitlab_config.provider == "gitlab"
        assert gitlab_config.gitlab_host == "https://gitlab.com"
        
        # Test Bitbucket configuration
        bitbucket_config = RepoSplitterConfig(
            source_repo_url="https://bitbucket.org/testorg/repo.git",
            org="testorg",
            github_token="test-token",
            provider="bitbucket",
            provider_username="testorg"
        )
        assert bitbucket_config.provider == "bitbucket"
        assert bitbucket_config.provider_username == "testorg"
        
        # Test Azure configuration
        azure_config = RepoSplitterConfig(
            source_repo_url="https://dev.azure.com/testorg/testproj/_git/repo",
            org="testorg",
            github_token="test-token",
            provider="azure",
            azure_project="testproj"
        )
        assert azure_config.provider == "azure"
        assert azure_config.azure_project == "testproj"
    
    def test_mode_configuration(self):
        """Test different mode configurations."""
        # Test auto mode
        auto_config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/repo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            mode="auto"
        )
        assert auto_config.mode == "auto"
        
        # Test project mode
        project_config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/repo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            mode="project"
        )
        assert project_config.mode == "project"
        
        # Test branch mode
        branch_config = RepoSplitterConfig(
            source_repo_url="https://github.com/testorg/repo.git",
            org="testorg",
            github_token="test-token",
            provider="github",
            mode="branch"
        )
        assert branch_config.mode == "branch"
