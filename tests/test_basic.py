import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from split_repo_agent import RepoSplitterConfig, RepoSplitter


class TestBasicFunctionality:
    """Test basic functionality of the repository splitter."""

    def test_config_creation(self):
        """Test basic configuration creation."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        assert config.source_repo_url == "git@github.com:test/repo.git"
        assert config.org == "test-org"
        assert config.github_token == "ghp_test123"
        assert config.mode == "auto"
        assert config.dry_run is False

    def test_config_with_options(self):
        """Test configuration with all options."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            mode="project",
            manual_projects=["app1", "app2"],
            common_path="shared",
            private_repos=True,
            dry_run=True
        )
        
        assert config.mode == "project"
        assert config.manual_projects == ["app1", "app2"]
        assert config.common_path == "shared"
        assert config.private_repos is True
        assert config.dry_run is True

    def test_sanitize_repo_name(self):
        """Test repository name sanitization."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        # Test basic sanitization
        assert splitter._sanitize_repo_name("My App") == "my-app"
        assert splitter._sanitize_repo_name("Frontend App") == "frontend-app"
        assert splitter._sanitize_repo_name("API Service") == "api-service"
        
        # Test special characters
        assert splitter._sanitize_repo_name("app@v2.0") == "app-v2.0"
        assert splitter._sanitize_repo_name("service#backend") == "service-backend"
        
        # Test edge cases
        assert splitter._sanitize_repo_name("") == "repo"
        assert splitter._sanitize_repo_name("   ") == "repo"

    def test_git_command_execution(self):
        """Test git command execution."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "git version 2.30.0"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = splitter.run_git_command(['git', '--version'])
            
            assert result.returncode == 0
            assert result.stdout == "git version 2.30.0"
            mock_run.assert_called_once()

    def test_git_command_failure(self):
        """Test git command failure handling."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Git command failed")
            
            with pytest.raises(Exception):
                splitter.run_git_command(['git', 'invalid-command'])

    def test_template_formatting(self):
        """Test template string formatting."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            repo_name_template_app="{name}-service",
            repo_name_template_lib="{name}-library"
        )
        
        # Test template formatting
        app_name = config.repo_name_template_app.format(name="frontend")
        lib_name = config.repo_name_template_lib.format(name="utils")
        
        assert app_name == "frontend-service"
        assert lib_name == "utils-library"

    def test_environment_loading(self):
        """Test loading configuration from environment variables."""
        with patch.dict(os.environ, {
            'SOURCE_REPO_URL': 'git@github.com:test/repo.git',
            'ORG': 'test-org',
            'GITHUB_TOKEN': 'ghp_test123',
            'MODE': 'project',
            'PROJECTS': 'app1,app2,app3'
        }):
            from split_repo_agent import RepoSplitter
            
            test_config = RepoSplitterConfig(
                source_repo_url="",
                org="",
                github_token="ghp_test123",
                dry_run=True
            )
            
            splitter = RepoSplitter(test_config)
            config = splitter.load_config()
            
            assert config.source_repo_url == "git@github.com:test/repo.git"
            assert config.org == "test-org"
            assert config.github_token == "ghp_test123"
            assert config.manual_projects == ["app1", "app2", "app3"]

    def test_error_handling(self):
        """Test error handling in utility functions."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        # Test sanitization with None input
        with pytest.raises(AttributeError):
            splitter._sanitize_repo_name(None)

    def test_unicode_handling(self):
        """Test handling of unicode characters."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        # Test with unicode
        assert splitter._sanitize_repo_name("app-émojis") == "app-mojis"
        assert splitter._sanitize_repo_name("服务") == "repo"  # Non-ASCII becomes repo
        assert splitter._sanitize_repo_name("app-ñ") == "app"  # ñ becomes empty, then repo

    def test_config_validation(self):
        """Test configuration validation."""
        # Test that config can be created with valid data
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        assert config is not None
        assert config.source_repo_url == "git@github.com:test/repo.git"

    def test_mode_handling(self):
        """Test different modes handling."""
        # Test auto mode
        config_auto = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            mode="auto"
        )
        assert config_auto.mode == "auto"
        
        # Test project mode
        config_project = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            mode="project",
            manual_projects=["app1", "app2"]
        )
        assert config_project.mode == "project"
        assert config_project.manual_projects == ["app1", "app2"]
        
        # Test branch mode
        config_branch = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            mode="branch",
            branches=["main", "develop"]
        )
        assert config_branch.mode == "branch"
        assert config_branch.branches == ["main", "develop"]
