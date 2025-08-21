# Project Mode Guide for libft Monorepo

This guide shows how to use the updated AI agent to split your libft monorepo into separate repositories.

## Your Current Structure

```
testmonorepo/
├── libft/           # Shared library (root level)
├── fractol/         # Project 1
├── printf/          # Project 2  
└── pushswap/        # Project 3
```

## Configuration for Project Mode

Edit the `.env` file with these settings:

```env
# Monorepo to split (your current repository)
SOURCE_REPO_URL=git@github.com:elenasurovtseva/testmonorepo.git

# Mode: project-based splitting
MODE=project

# Projects to extract (your current projects)
PROJECTS=fractol,printf,pushswap

# Common library path
COMMON_PATH=libft

# GitHub organization or username
ORG=elenasurovtseva

# GitHub Personal Access Token with repo scope
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## What the Agent Will Do

1. **Clone your monorepo** as a mirror to preserve all history
2. **Create 4 new repositories**:
   - `fractol-app` (extracted from `fractol/` directory)
   - `printf-app` (extracted from `printf/` directory)  
   - `pushswap-app` (extracted from `pushswap/` directory)
   - `common-libs` (extracted from `libft/` directory)

3. **Preserve git history** for each extracted project
4. **Maintain the shared library** as a separate repository

## Usage Steps

1. **Setup the environment**:
   ```bash
   cd morethaneternity-project-main
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure the agent**:
   ```bash
   # Copy the example configuration
   cp env.example .env
   
   # Edit .env with your actual values
   nano .env
   ```

3. **Test the configuration**:
   ```bash
   python test_config.py
   ```

4. **Dry run (test mode)**:
   ```bash
   python split_repo_agent.py --dry-run --mode project
   ```

5. **Actual execution**:
   ```bash
   python split_repo_agent.py --mode project
   ```

## Expected Output

After running the agent, you'll have these new repositories:

```
elenasurovtseva/
├── fractol-app/     # Contains only fractol/ files with history
├── printf-app/      # Contains only printf/ files with history
├── pushswap-app/    # Contains only pushswap/ files with history
└── common-libs/     # Contains only libft/ files with history
```

## Benefits

- **No more code duplication** - each project has its own repository
- **Shared library** - libft is available as a separate repository
- **Preserved history** - all git commits are maintained
- **Clean separation** - each project can be developed independently
- **Easy dependency management** - projects can reference the common-libs repository

## After Splitting

Once the repositories are created, you can:

1. **Clone each repository**:
   ```bash
   git clone https://github.com/elenasurovtseva/fractol-app.git
   git clone https://github.com/elenasurovtseva/printf-app.git
   git clone https://github.com/elenasurovtseva/pushswap-app.git
   git clone https://github.com/elenasurovtseva/common-libs.git
   ```

2. **Update Makefiles** to reference the common-libs repository as a submodule or dependency

3. **Continue development** in the separate repositories

## Troubleshooting

- **GitHub Token**: Make sure your token has `repo` scope
- **Repository Access**: Ensure you have write access to create repositories
- **SSH Keys**: If using SSH URLs, ensure SSH keys are configured
- **Dry Run**: Always test with `--dry-run` first

## Example Output

```
2024-01-15 10:30:00 - INFO - Configuration loaded: mode=project, org: elenasurovtseva
2024-01-15 10:30:01 - INFO - Cloning source repository: git@github.com:elenasurovtseva/testmonorepo.git
2024-01-15 10:30:05 - INFO - Analyzing for common files...
2024-01-15 10:30:06 - INFO - Found 5 common files across all projects
2024-01-15 10:30:07 - INFO - Processing project: fractol
2024-01-15 10:30:08 - INFO - Created repository: fractol-app
2024-01-15 10:30:12 - INFO - Successfully extracted project 'fractol' to 'fractol-app'
2024-01-15 10:30:12 - INFO - Repository URL: https://github.com/elenasurovtseva/fractol-app.git
...
2024-01-15 10:35:00 - INFO - ==================================================
2024-01-15 10:35:00 - INFO - REPOSITORY SPLITTING COMPLETED
2024-01-15 10:35:00 - INFO - ==================================================
2024-01-15 10:35:00 - INFO - Created 4 repositories:
2024-01-15 10:35:00 - INFO -   - fractol-app
2024-01-15 10:35:00 - INFO -   - printf-app
2024-01-15 10:35:00 - INFO -   - pushswap-app
2024-01-15 10:35:00 - INFO -   - common-libs
```
