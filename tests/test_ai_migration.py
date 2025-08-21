"""Tests for package.json migration transformer."""

import json
from split_repo_agent import RepoSplitter


class TestPackageJsonMigration:
    def test_transform_basic_fields_app(self):
        original = {
            "name": "",
            "scripts": {}
        }
        migrated = RepoSplitter._transform_package_json(
            original,
            repo_name="frontend-app",
            repo_url="https://github.com/org/frontend-app.git",
            is_library=False,
        )
        assert migrated["name"] == "frontend-app"
        assert migrated["version"] == "1.0.0"
        assert migrated["repository"]["url"].endswith("frontend-app.git")
        assert migrated["private"] is False
        assert "test" in migrated["scripts"]
        assert "build" in migrated["scripts"]

    def test_transform_preserve_existing(self):
        original = {
            "name": "custom",
            "version": "0.9.0",
            "repository": {"type": "git", "url": "https://example.com/custom.git"},
            "scripts": {"test": "jest"},
            "private": True,
            "workspaces": ["packages/*"],
        }
        migrated = RepoSplitter._transform_package_json(
            original,
            repo_name="lib-utils",
            repo_url="https://github.com/org/lib-utils.git",
            is_library=True,
        )
        assert migrated["name"] == "custom"
        assert migrated["version"] == "0.9.0"
        assert migrated["repository"]["url"] == "https://example.com/custom.git"
        assert migrated.get("private") is True  # preserved for libraries
        assert "workspaces" not in migrated  # removed for standalone repo
        assert migrated["scripts"]["test"] == "jest"

    def test_transform_sets_homepage(self):
        original = {}
        migrated = RepoSplitter._transform_package_json(
            original,
            repo_name="api-app",
            repo_url="https://github.com/org/api-app.git",
            is_library=False,
        )
        assert migrated["homepage"] == "https://github.com/org/api-app"
