#!/usr/bin/env python3
"""
Force update existing repositories with correct content.

This script re-extracts configured projects/common libs from the monorepo and force-pushes
them to their corresponding repositories, respecting default branch and naming templates.
"""

import os
import re
from split_repo_agent import RepoSplitter, RepoSplitterConfig

def _sanitize_repo_name(raw_name: str) -> str:
    name = raw_name.strip().lower()
    name = re.sub(r"[^a-z0-9._-]", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-._") or "repo"


def force_update_repositories():
    """Force update existing repositories with correct content."""
    from dotenv import load_dotenv
    load_dotenv()

    config = RepoSplitterConfig(
        source_repo_url=os.getenv('SOURCE_REPO_URL'),
        org=os.getenv('ORG'),
        github_token=os.getenv('GITHUB_TOKEN'),
        mode='project',
        manual_projects=[p.strip() for p in os.getenv('PROJECTS', '').split(',') if p.strip()],
        common_path=(os.getenv('COMMON_PATH') or None),
        default_branch=os.getenv('DEFAULT_BRANCH', 'main'),
        repo_name_template_app=os.getenv('REPO_NAME_TEMPLATE_APP', '{name}-app'),
        repo_name_template_lib=os.getenv('REPO_NAME_TEMPLATE_LIB', '{name}-lib'),
        dry_run=False
    )

    if not config.manual_projects:
        raise ValueError("PROJECTS must be set to use force_update_repos in project mode")

    with RepoSplitter(config) as splitter:
        splitter.clone_source_repo()

        # Force update each project
        for project_path in config.manual_projects:
            project_name = os.path.basename(project_path)
            repo_name = _sanitize_repo_name(config.repo_name_template_app.format(name=project_name))
            repo_url = f"https://github.com/{config.org}/{repo_name}.git"

            print(f"Force updating {repo_name}...")

            # Extract project to temp directory
            project_repo_path = os.path.join(splitter.temp_dir, f"project_{project_name}")

            # Clone the mirror repo
            splitter.run_git_command(['git', 'clone', splitter.source_repo_path, project_repo_path])

            # Validate project path exists
            if not os.path.exists(os.path.join(project_repo_path, project_path)):
                print(f"Warning: Project directory '{project_path}' not found")
                continue

            # Use git filter-repo to extract only the project path
            splitter.run_git_command([
                'git', 'filter-repo',
                '--path', f'{project_path}/',
                '--path-rename', f'{project_path}/:',
                '--force'
            ], cwd=project_repo_path)

            # Ensure default branch exists and set as current
            splitter.run_git_command(['git', 'branch', '-M', config.default_branch], cwd=project_repo_path)

            # Remove remote origin if it exists
            splitter.run_git_command(['git', 'remote', 'remove', 'origin'], check=False, cwd=project_repo_path)

            # Add new remote
            splitter.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=project_repo_path)

            # Force push to update the repository
            splitter.run_git_command(['git', 'push', '-f', 'origin', config.default_branch], cwd=project_repo_path)

            print(f"✅ Updated {repo_name}")

        # Force update common libraries
        if config.common_path:
            comp_name = os.path.basename(config.common_path)
            repo_name = _sanitize_repo_name(config.repo_name_template_lib.format(name=comp_name))
            repo_url = f"https://github.com/{config.org}/{repo_name}.git"

            print(f"Force updating {repo_name}...")

            common_repo_path = os.path.join(splitter.temp_dir, f"component_{comp_name}")

            # Clone the mirror repo
            splitter.run_git_command(['git', 'clone', splitter.source_repo_path, common_repo_path])

            if not os.path.exists(os.path.join(common_repo_path, config.common_path)):
                print(f"Warning: Common path '{config.common_path}' not found")
                return

            # Use git filter-repo to extract only the common path
            splitter.run_git_command([
                'git', 'filter-repo',
                '--path', f'{config.common_path}/',
                '--path-rename', f'{config.common_path}/:',
                '--force'
            ], cwd=common_repo_path)

            # Ensure default branch
            splitter.run_git_command(['git', 'branch', '-M', config.default_branch], cwd=common_repo_path)

            # Remove and add remote
            splitter.run_git_command(['git', 'remote', 'remove', 'origin'], check=False, cwd=common_repo_path)
            splitter.run_git_command(['git', 'remote', 'add', 'origin', repo_url], cwd=common_repo_path)

            # Force push
            splitter.run_git_command(['git', 'push', '-f', 'origin', config.default_branch], cwd=common_repo_path)

            print(f"✅ Updated {repo_name}")

if __name__ == "__main__":
    force_update_repositories()
