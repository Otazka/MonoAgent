# Troubleshooting Guide

This guide helps diagnose and resolve common issues when running the GitHub Monorepo Splitter AI Agent.

## 1) Quick checks (preflight)

Verify prerequisites:

```bash
# Git & git-filter-repo
git --version
git filter-repo --help  # should print usage

# Python
python -V  # >= 3.9

# Graphviz (for --visualize)
dot -V
```

Verify environment:

```bash
# Required
printenv SOURCE_REPO_URL  # e.g., git@github.com:org/monorepo.git
printenv ORG              # org or username
printenv GITHUB_TOKEN     # token with repo scope
```

Run a safe preview:

```bash
python split_repo_agent.py --analyze-only --dry-run
```

## 2) Common errors and fixes

### GitHub 401/403 (Unauthorized/Forbidden)
- **cause**: Invalid token, missing scopes, or SSO not authorized.
- **fix**:
  - Create a token with `repo` scope.
  - Authorize SSO for the token if your org requires it.
  - Test: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user` should return your user.

### GitHub 404 (Organization or repo)
- **cause**: `ORG` is wrong or token lacks org access.
- **fix**:
  - Confirm `ORG` in `.env`.
  - Ensure the token has org access or use a user-owned repository fallback.

### GitHub rate limit exceeded / abuse detection
- **symptoms**: 403 with rate-limit/abuse messages.
- **what happens**: Tool automatically waits until reset or `Retry-After` header.
- **fix**:
  - Wait for reset (the tool logs how long it waits).
  - Reduce operation frequency.
  - Tune in `.env`:
    - `rate_limit_min_remaining=50`
    - `abuse_retry_after_default=60`

### `git-filter-repo` not found
- **cause**: The binary is missing.
- **fix**:
  - macOS (Homebrew): `brew install git-filter-repo`
  - pip: `pip install git-filter-repo`

### Project path does not exist
- **cause**: Wrong `PROJECTS` path or unexpected layout.
- **fix**:
  - Run `--analyze-only` to see detected projects.
  - Double-check directory names; use exact paths as listed by analysis.

### Branch not found
- **cause**: Provided branch name not present.
- **fix**:
  - List remote branches: `git ls-remote --heads <SOURCE_REPO_URL>`
  - Use the exact branch name.

### Visualization failed (Graphviz)
- **cause**: `dot` is not installed.
- **fix**:
  - `brew install graphviz` (macOS) or appropriate package for your OS.
  - Re-run with `--visualize`.

## 3) Logs & diagnostics
- Log file: `repo_splitter.log` contains detailed steps and errors.
- Analysis report: `monorepo_analysis.json` summarizes detected projects, components, dependencies, conflicts, and AI insights.
- Run with `--analyze-only --dry-run` before making changes.

## 4) Configuration reference (selected)
- `SOURCE_REPO_URL`: Git URL of the monorepo (required)
- `ORG`: GitHub org or username (required)
- `GITHUB_TOKEN`: Token with `repo` scope (required)
- `MODE`: `auto` | `project` | `branch`
- `PROJECTS`: Comma-separated list (project mode)
- `BRANCHES`: Comma-separated list (branch mode)
- `PRIVATE_REPOS`: `true|false`
- `DEFAULT_BRANCH`: e.g., `main`
- `rate_limit_min_remaining`: Wait if remaining core calls <= this value (default 50)
- `abuse_retry_after_default`: Fallback wait seconds for abuse/secondary limit (default 60)

## 5) Support tips
- Always preview with `--analyze-only --dry-run`.
- Use `--force` only when you understand conflicts.
- If failing repeatedly, open an issue with the log file and your command/flags.
