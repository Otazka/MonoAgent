# GitHub Monorepo Splitter AI Agent

A Python-based AI agent that automatically splits a GitHub monorepo into multiple repositories, preserving git history for each branch and common libraries.

## Features

- **Automatic Repository Creation**: Creates new GitHub repositories via API
- **History Preservation**: Maintains complete git history for each extracted branch
- **Branch Extraction**: Extracts each specified branch into its own repository
- **Common Libraries**: Extracts shared code into a separate `common-libs` repository
- **AI-Powered Analysis**: Optional analysis to identify common files across branches
- **Dry Run Mode**: Test the process without making actual changes
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

## Requirements

- Python 3.9+
- Git installed and available in PATH
- `git-filter-repo` installed and available in PATH
- GitHub Personal Access Token with repo scope

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install git-filter-repo**:
   ```bash
   # On macOS with Homebrew
   brew install git-filter-repo
   
   # On Ubuntu/Debian
   sudo apt-get install git-filter-repo
   
   # On Windows with Chocolatey
   choco install git-filter-repo
   
   # Or install via pip
   pip install git-filter-repo
   ```

4. **Configure the environment**:
   ```bash
   # The .env file is already created - edit it with your configuration
   nano .env
   # or
   code .env
   ```

## Configuration

The `.env` file is already created. Edit it with your configuration values:

### Required Variables

- `SOURCE_REPO_URL`: SSH or HTTPS URL of the monorepo to split
- `BRANCHES`: Comma-separated list of branch names (each becomes a separate app)
- `ORG`: GitHub organization or username to host the new repositories
- `GITHUB_TOKEN`: GitHub Personal Access Token with repo scope

### Optional Variables

- `COMMON_PATH`: Path to common libraries folder (extracted to `common-libs` repo)
- `OPENAI_API_KEY`: OpenAI API key for AI-powered common file analysis

### Example Configuration

```env
# Monorepo to split (SSH or HTTPS URL)
SOURCE_REPO_URL=git@github.com:mycompany/monorepo.git

# Comma-separated list of branch names (apps)
BRANCHES=frontend,backend,mobile,admin,api

# Path for common libraries inside the repo (optional)
COMMON_PATH=shared/

# GitHub organization or username to create new repos under
ORG=mycompany

# GitHub Personal Access Token with repo scope
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Optional: OpenAI API Key for AI-powered common file analysis
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Usage

### Quick Start

1. **Setup Environment** (if not already done):
   ```bash
   cd aiAgent
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Test your configuration**:
   ```bash
   python test_config.py
   ```

3. **Run the Agent**:

   **Option 1: Using the run script (Recommended)**:
   ```bash
   # Dry run (test mode)
   ./run.sh --dry-run
   
   # Actual execution
   ./run.sh
   ```

   **Option 2: Direct Python execution**:
   ```bash
   # Dry run (test mode)
   source venv/bin/activate && python split_repo_agent.py --dry-run
   
   # Actual execution
   source venv/bin/activate && python split_repo_agent.py
   ```

### Programmatic Usage

You can also use the agent programmatically:

```python
from split_repo_agent import RepoSplitter, RepoSplitterConfig

config = RepoSplitterConfig(
    source_repo_url="git@github.com:org/monorepo.git",
    branches=["app1", "app2", "app3", "app4", "app5"],
    common_path="shared/",
    org="my-org",
    github_token="ghp_xxx",
    dry_run=False
)

with RepoSplitter(config) as splitter:
    splitter.split_repositories()
```

### Example Output

```
2024-01-15 10:30:00 - INFO - Configuration loaded: 5 branches, org: mycompany
2024-01-15 10:30:01 - INFO - Cloning source repository: git@github.com:mycompany/monorepo.git
2024-01-15 10:30:05 - INFO - Analyzing branches for common files...
2024-01-15 10:30:06 - INFO - Found 15 common files across all branches
2024-01-15 10:30:07 - INFO - Processing branch: frontend
2024-01-15 10:30:08 - INFO - Created repository: frontend-app
2024-01-15 10:30:12 - INFO - Successfully extracted branch 'frontend' to 'frontend-app'
2024-01-15 10:30:12 - INFO - Repository URL: https://github.com/mycompany/frontend-app.git
...
2024-01-15 10:35:00 - INFO - ==================================================
2024-01-15 10:35:00 - INFO - REPOSITORY SPLITTING COMPLETED
2024-01-15 10:35:00 - INFO - ==================================================
2024-01-15 10:35:00 - INFO - Created 6 repositories:
2024-01-15 10:35:00 - INFO -   - frontend-app
2024-01-15 10:35:00 - INFO -   - backend-app
2024-01-15 10:35:00 - INFO -   - mobile-app
2024-01-15 10:35:00 - INFO -   - admin-app
2024-01-15 10:35:00 - INFO -   - api-app
2024-01-15 10:35:00 - INFO -   - common-libs
```

## How It Works

### 1. Repository Cloning
- Clones the source monorepo as a mirror to preserve all history
- Uses temporary directories for processing

### 2. Branch Extraction
For each branch in the `BRANCHES` configuration:
- Creates a new GitHub repository via API
- Extracts only that branch's history
- Renames the branch to `main`
- Pushes the complete history to the new repository

### 3. Common Libraries Extraction
If `COMMON_PATH` is specified:
- Uses `git filter-repo` to extract only files from the specified path
- Creates a `common-libs` repository
- Preserves history for the extracted files

### 4. AI Analysis (Optional)
- Analyzes file trees across all branches
- Identifies common files that might be candidates for shared libraries
- Provides suggestions for what could be moved to `COMMON_PATH`

## Repository Structure

After splitting, you'll have:

```
mycompany/
├── frontend-app/     # Extracted from frontend branch
├── backend-app/      # Extracted from backend branch
├── mobile-app/       # Extracted from mobile branch
├── admin-app/        # Extracted from admin branch
├── api-app/          # Extracted from api branch
└── common-libs/      # Extracted from COMMON_PATH
```

## Project Structure

```
aiAgent/
├── split_repo_agent.py    # Main agent script
├── test_config.py         # Configuration validation script
├── example_usage.py       # Programmatic usage example
├── requirements.txt       # Python dependencies
├── .env                   # Configuration file (edit this)
├── .gitignore            # Git ignore rules
└── README.md             # This documentation
```

## Error Handling

The agent includes comprehensive error handling:

- **Validation**: Checks all required configuration variables
- **Git Operations**: Handles git command failures gracefully
- **GitHub API**: Manages API rate limits and authentication errors
- **Cleanup**: Automatically removes temporary files on completion or error
- **Logging**: Detailed logs saved to `repo_splitter.log`

## Security Considerations

- **GitHub Token**: Use a Personal Access Token with minimal required scopes (`repo` scope)
- **SSH Keys**: Ensure SSH keys are properly configured for private repositories
- **Temporary Files**: All temporary files are automatically cleaned up
- **Dry Run**: Always test with `--dry-run` first
- **Environment File**: Never commit `.env` file to version control (it's already in `.gitignore`)

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**
   - The agent handles rate limits automatically
   - Consider using a GitHub App token for higher limits

2. **SSH Authentication**
   - Ensure SSH keys are added to your GitHub account
   - Test SSH connection: `ssh -T git@github.com`

3. **git-filter-repo Not Found**
   - Install git-filter-repo: `pip install git-filter-repo`
   - Ensure it's available in your PATH

4. **Permission Denied**
   - Verify GitHub token has `repo` scope
   - Check organization permissions if creating repos in an org

### Debug Mode

Enable debug logging by modifying the script:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `repo_splitter.log`
3. Run `python test_config.py` to validate your setup
4. Create an issue with detailed error information

## Next Steps

After setting up your configuration:

1. **Edit `.env`** with your actual values
2. **Run `python test_config.py`** to validate everything
3. **Test with `python split_repo_agent.py --dry-run`**
4. **Execute with `python split_repo_agent.py`**

The agent will create 6 repositories total:
- 5 app repositories (one for each branch)
- 1 common-libs repository (if `COMMON_PATH` is specified)
