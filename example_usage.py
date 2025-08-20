#!/usr/bin/env python3
"""
Example usage of the GitHub Monorepo Splitter AI Agent

This script demonstrates how to use the RepoSplitter class programmatically
instead of using the command-line interface.
"""

import os
from split_repo_agent import RepoSplitter, RepoSplitterConfig


def main():
    """Example of programmatic usage."""
    
    # Example configuration
    config = RepoSplitterConfig(
        source_repo_url="git@github.com:example-org/monorepo.git",
        branches=["frontend", "backend", "mobile", "admin", "api"],
        common_path="shared/",
        org="example-org",
        github_token=os.getenv("GITHUB_TOKEN"),
        dry_run=True  # Set to False for actual execution
    )
    
    # Create and run the splitter
    with RepoSplitter(config) as splitter:
        try:
            splitter.split_repositories()
            print("Repository splitting completed successfully!")
        except Exception as e:
            print(f"Error during splitting: {e}")


if __name__ == "__main__":
    main()
