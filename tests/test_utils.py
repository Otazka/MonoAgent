import pytest
import subprocess
from unittest.mock import patch, MagicMock
from split_repo_agent import RepoSplitter, RepoSplitterConfig


class TestUtils:
    """Test utility functions."""

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
        
        # Test special characters - the actual implementation preserves dots
        assert splitter._sanitize_repo_name("app@v2.0") == "app-v2.0"
        assert splitter._sanitize_repo_name("service#backend") == "service-backend"
        assert splitter._sanitize_repo_name("lib/utils.js") == "lib-utils.js"  # Dots are preserved
        
        # Test edge cases
        assert splitter._sanitize_repo_name("") == "repo"
        assert splitter._sanitize_repo_name("   ") == "repo"
        assert splitter._sanitize_repo_name("---") == "repo"
        assert splitter._sanitize_repo_name("a") == "a"
        
        # Test multiple hyphens
        assert splitter._sanitize_repo_name("app--service") == "app-service"
        assert splitter._sanitize_repo_name("frontend---backend") == "frontend-backend"

    def test_run_git_command_success(self):
        """Test successful git command execution."""
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

    def test_run_git_command_failure(self):
        """Test git command failure handling."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=['git', 'invalid-command'],
                stderr="fatal: unknown command 'invalid-command'"
            )
            
            with pytest.raises(subprocess.CalledProcessError):
                splitter.run_git_command(['git', 'invalid-command'])

    def test_run_git_command_with_cwd(self):
        """Test git command execution with custom working directory."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = "On branch main"
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            result = splitter.run_git_command(['git', 'branch'], cwd="/tmp/test")
            
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[1]['cwd'] == "/tmp/test"

    def test_run_git_command_no_check(self):
        """Test git command execution without checking return code."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "fatal: not a git repository"
            mock_run.return_value = mock_result
            
            result = splitter.run_git_command(['git', 'status'], check=False)
            
            assert result.returncode == 1
            assert result.stderr == "fatal: not a git repository"


class TestTemplateFormatting:
    """Test template string formatting for repository names."""

    def test_repo_name_template_app(self):
        """Test app repository name template formatting."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            repo_name_template_app="{name}-service"
        )
        
        splitter = RepoSplitter(config)
        
        # Test template formatting
        repo_name = config.repo_name_template_app.format(name="frontend")
        sanitized = splitter._sanitize_repo_name(repo_name)
        
        assert repo_name == "frontend-service"
        assert sanitized == "frontend-service"

    def test_repo_name_template_lib(self):
        """Test library repository name template formatting."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            repo_name_template_lib="{name}-library"
        )
        
        splitter = RepoSplitter(config)
        
        # Test template formatting
        repo_name = config.repo_name_template_lib.format(name="utils")
        sanitized = splitter._sanitize_repo_name(repo_name)
        
        assert repo_name == "utils-library"
        assert sanitized == "utils-library"

    def test_custom_templates(self):
        """Test custom repository name templates."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123",
            repo_name_template_app="{name}-app-v2",
            repo_name_template_lib="{name}-core"
        )
        
        splitter = RepoSplitter(config)
        
        # Test app template
        app_name = config.repo_name_template_app.format(name="backend")
        app_sanitized = splitter._sanitize_repo_name(app_name)
        assert app_sanitized == "backend-app-v2"
        
        # Test lib template
        lib_name = config.repo_name_template_lib.format(name="database")
        lib_sanitized = splitter._sanitize_repo_name(lib_name)
        assert lib_sanitized == "database-core"


class TestErrorHandling:
    """Test error handling in utility functions."""

    def test_sanitize_repo_name_with_none(self):
        """Test sanitization with None input."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        with pytest.raises(AttributeError):
            splitter._sanitize_repo_name(None)

    def test_sanitize_repo_name_with_numbers(self):
        """Test sanitization with numeric input."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        # Test with numbers
        assert splitter._sanitize_repo_name("app123") == "app123"
        assert splitter._sanitize_repo_name("123app") == "123app"
        assert splitter._sanitize_repo_name("app-123") == "app-123"

    def test_sanitize_repo_name_with_unicode(self):
        """Test sanitization with unicode characters."""
        config = RepoSplitterConfig(
            source_repo_url="git@github.com:test/repo.git",
            org="test-org",
            github_token="ghp_test123"
        )
        
        splitter = RepoSplitter(config)
        
        # Test with unicode - the actual implementation removes non-ASCII
        assert splitter._sanitize_repo_name("app-émojis") == "app-mojis"
        assert splitter._sanitize_repo_name("服务") == "repo"  # Non-ASCII becomes repo
        assert splitter._sanitize_repo_name("app-ñ") == "app"  # ñ becomes empty, then repo
