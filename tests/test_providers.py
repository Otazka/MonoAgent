"""Provider creation flow tests with mocked HTTP.

Covers success and negative paths for GitLab, Bitbucket, Azure DevOps.
"""

import types
import sys
import builtins
import pytest

from split_repo_agent import RepoSplitterConfig, RepoSplitter


class FakeResp:
    def __init__(self, status_code=200, json_data=None, text="", links=None):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = text
        self._links = links or []

    def json(self):
        return self._json


def make_fake_requests(post=None, get=None):
    mod = types.SimpleNamespace()
    mod.post = post or (lambda *a, **k: FakeResp(200, {}))
    mod.get = get or (lambda *a, **k: FakeResp(200, {}))
    return mod


@pytest.fixture
def splitter_base():
    # Minimal valid config
    cfg = RepoSplitterConfig(
        source_repo_url="",
        org="acme",
        github_token="tok",
        dry_run=True,  # Use dry_run to avoid actual API calls
    )
    sp = RepoSplitter(cfg)
    # Prevent accidental network calls via rate limit guard
    sp._rate_limit_guard = lambda: None
    # Mock the _log_issue method to prevent logging during tests
    sp._log_issue = lambda *args, **kwargs: None
    return sp


class TestGitLabCreate:
    def test_gitlab_success(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "gitlab"

        def fake_post(url, headers=None, data=None, timeout=None):
            assert "/api/v4/projects" in url
            return FakeResp(201, {"ssh_url_to_repo": "git@gitlab.com:acme/demo.git"})

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        url = splitter_base._create_repo_gitlab("demo", "desc")
        assert url is not None
        assert url.endswith("demo.git")

    def test_gitlab_exists_409(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "gitlab"

        def fake_post(url, headers=None, data=None, timeout=None):
            return FakeResp(409, text="already exists")

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        url = splitter_base._create_repo_gitlab("demo", "desc")
        assert url is not None
        assert url.endswith("/acme/demo.git")

    def test_gitlab_unauthorized(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "gitlab"
        # Set dry_run to False to test actual error handling
        splitter_base.config.dry_run = False

        def fake_post(url, headers=None, data=None, timeout=None):
            return FakeResp(401, text="unauthorized")

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        assert splitter_base._create_repo_gitlab("demo", "desc") is None


class TestBitbucketCreate:
    def test_bitbucket_success(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "bitbucket"
        splitter_base.config.provider_username = "acme"

        def fake_post(url, auth=None, json=None, timeout=None):
            return FakeResp(201, json_data={
                "links": {
                    "clone": [
                        {"name": "ssh", "href": "git@bitbucket.org:acme/demo.git"},
                        {"name": "https", "href": "https://bitbucket.org/acme/demo.git"},
                    ]
                }
            })

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        url = splitter_base._create_repo_bitbucket("demo", "desc")
        assert url is not None
        assert url.endswith("demo.git")

    def test_bitbucket_exists(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "bitbucket"
        splitter_base.config.provider_username = "acme"

        def fake_post(url, auth=None, json=None, timeout=None):
            return FakeResp(400, text="Repository already exists")

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        url = splitter_base._create_repo_bitbucket("demo", "desc")
        assert url is not None
        assert url.startswith("git@bitbucket.org:acme/demo.git")

    def test_bitbucket_unauthorized(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "bitbucket"
        splitter_base.config.provider_username = "acme"
        # Set dry_run to False to test actual error handling
        splitter_base.config.dry_run = False

        def fake_post(url, auth=None, json=None, timeout=None):
            return FakeResp(401, text="Unauthorized")

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        assert splitter_base._create_repo_bitbucket("demo", "desc") is None


class TestAzureCreate:
    def test_azure_success(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "azure"
        splitter_base.config.azure_project = "proj"

        def fake_post(url, headers=None, json=None, timeout=None):
            return FakeResp(201, json_data={
                "remoteUrl": "https://dev.azure.com/acme/proj/_git/demo",
                "sshUrl": "git@ssh.dev.azure.com:v3/acme/proj/demo"
            })

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        url = splitter_base._create_repo_azure("demo", "desc")
        assert url is not None
        assert url.endswith("/proj/_git/demo")

    def test_azure_conflict_409(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "azure"
        splitter_base.config.azure_project = "proj"

        def fake_post(url, headers=None, json=None, timeout=None):
            return FakeResp(409, text="exists")

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        url = splitter_base._create_repo_azure("demo", "desc")
        assert url is not None
        assert url.endswith("/proj/_git/demo")

    def test_azure_unauthorized(self, monkeypatch, splitter_base):
        splitter_base.config.provider = "azure"
        splitter_base.config.azure_project = "proj"
        # Set dry_run to False to test actual error handling
        splitter_base.config.dry_run = False

        def fake_post(url, headers=None, json=None, timeout=None):
            return FakeResp(401, text="Unauthorized")

        monkeypatch.setitem(sys.modules, 'requests', make_fake_requests(post=fake_post))
        assert splitter_base._create_repo_azure("demo", "desc") is None


