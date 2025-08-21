# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0-beta] - 2025-08-21

### Added
- AI-powered analysis: dependency conflict detection (version/missing/circular/shared), actionable recommendations, complexity/readiness scores.
- Dependency graph visualization (PNG/DOT/SVG) with conflict highlighting.
- Universal splitting modes: `auto`, `project`, `branch`.
- Multi-provider (beta): GitHub, GitLab, Bitbucket Cloud, Azure DevOps.
- Preflight checks for binaries (git, git-filter-repo, graphviz), repo reachability, and provider token validation.
- Rate limit guard and abuse backoff for GitHub API calls.
- `package.json` migration when extracting Node.js projects/components.
- Dockerfile for containerized execution.
- Comprehensive test suite (67 tests) and CI workflow.
- Troubleshooting guide and Golden Path quickstart.

### Changed
- Standardized and more actionable error messages in configuration load and workflows.

### Documentation
- Provider-specific env templates and Docker usage.
- Badges and improved Quick Start.

[1.0.0-beta]: https://github.com/Otazka/MonoAgent/releases/tag/v1.0.0-beta
