#!/usr/bin/env python3
"""
Example usage of the GitHub Monorepo Splitter AI Agent

This file demonstrates how to use the agent programmatically
for both branch and project modes.
"""

from split_repo_agent import RepoSplitter, RepoSplitterConfig


def example_branch_mode():
    """Example of branch-based splitting."""
    print("=== Branch Mode Example ===")
    
    config = RepoSplitterConfig(
        source_repo_url="git@github.com:mycompany/monorepo.git",
        mode="branch",
        branches=["frontend", "backend", "mobile", "admin", "api"],
        common_path="shared/",
        org="mycompany",
        github_token="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        dry_run=True  # Set to False for actual execution
    )
    
    with RepoSplitter(config) as splitter:
        splitter.split_repositories()


def example_project_mode():
    """Example of project-based splitting (like your libft case)."""
    print("=== Project Mode Example ===")
    
    config = RepoSplitterConfig(
        source_repo_url="git@github.com:mycompany/testmonorepo.git",
        mode="project",
        projects=["fractol", "printf", "pushswap"],
        common_path="libft",
        org="mycompany",
        github_token="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        dry_run=True  # Set to False for actual execution
    )
    
    with RepoSplitter(config) as splitter:
        splitter.split_repositories()


def main():
    """Run examples."""
    print("GitHub Monorepo Splitter AI Agent - Examples")
    print("=" * 50)
    
    # Uncomment the example you want to run
    example_branch_mode()
    # example_project_mode()


if __name__ == "__main__":
    main()
