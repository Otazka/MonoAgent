# Advanced GitHub Monorepo Splitter AI Agent

A Python-based AI agent that intelligently analyzes and splits GitHub monorepos into multiple repositories, handling complex scenarios:

- **Different apps on the same branch** → Separate into different repos
- **Common/generic components** → Separate into shared library repos  
- **Different apps on separate branches** → Each app gets its own repo
- **Intelligent project structure detection** and analysis
- **AI-powered dependency analysis** and recommendations

## Features

- **🤖 AI-Powered Analysis**: Automatically detects projects, apps, and common components
- **📁 Intelligent Project Detection**: Recognizes Node.js, Python, Java, Go, Rust, and more
- **🔧 Common Component Extraction**: Identifies and extracts shared libraries and utilities
- **🌿 Multi-Branch Support**: Handles different apps on separate branches
- **📊 Dependency Analysis**: Analyzes relationships between projects and components
- **📋 Comprehensive Reports**: Generates detailed analysis reports with recommendations
- **🔒 History Preservation**: Maintains complete git history for all extracted repositories
- **🧪 Dry Run Mode**: Test the process without making actual changes
- **📝 Detailed Logging**: Comprehensive logs for debugging and monitoring

## Use Cases

### 🎯 Complex Monorepo Scenarios

The AI agent handles various monorepo structures automatically:

#### **Scenario 1: Multiple Apps on Same Branch**
```
monorepo/
├── apps/
│   ├── frontend/     (React app)
│   ├── backend/      (Node.js API)
│   └── mobile/       (React Native)
├── shared/
│   ├── components/   (shared UI components)
│   └── utils/        (common utilities)
└── docs/
```

**Result**: 5 separate repositories
- `frontend-app`
- `backend-app` 
- `mobile-app`
- `components-lib`
- `utils-lib`

#### **Scenario 2: Different Apps on Different Branches**
```
monorepo/
├── main/             (main branch)
│   ├── web-app/
│   └── shared-libs/
├── mobile/           (mobile branch)
│   └── mobile-app/
└── api/              (api branch)
    └── backend-api/
```

**Result**: 4 separate repositories
- `web-app` (from main branch)
- `shared-libs` (from main branch)
- `mobile-app` (from mobile branch)
- `backend-api` (from api branch)

#### **Scenario 3: Mixed Structure with Common Components**
```
monorepo/
├── services/
│   ├── auth-service/
│   ├── user-service/
│   └── payment-service/
├── frontend/
│   ├── admin-panel/
│   └── customer-portal/
├── common/
│   ├── database/
│   ├── logging/
│   └── auth/
└── infrastructure/
```

**Result**: 9 separate repositories
- `auth-service-app`
- `user-service-app`
- `payment-service-app`
- `admin-panel-app`
- `customer-portal-app`
- `database-lib`
- `logging-lib`
- `auth-lib`
- `infrastructure-app`

## Requirements

- Python 3.9+
- Git installed and available in PATH
- `git-filter-repo` installed and available in PATH
- GitHub Personal Access Token with repo scope

## Installation

1. **Clone or download this repository**

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate     # On Windows
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install git-filter-repo**:
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

5. **Configure the environment**:
   ```bash
   # Copy the example configuration
   cp env.example .env
   
   # Edit the .env file with your configuration
   nano .env
   # or
   code .env
   ```

## Configuration

The `.env` file is already created. Edit it with your configuration values:

### Required Variables

- `SOURCE_REPO_URL`: SSH or HTTPS URL of the monorepo to split
- `ORG`: GitHub organization or username to host the new repositories
- `GITHUB_TOKEN`: GitHub Personal Access Token with repo scope

### Mode and Splitting Options

- `MODE`: `auto` | `branch` | `project`
  - `auto`: Detect projects and shared components automatically
  - `branch`: Split one repo per branch listed in `BRANCHES`
  - `project`: Split one repo per project path listed in `PROJECTS`
- `BRANCHES`: Comma-separated list of branches (for `MODE=branch`)
- `PROJECTS`: Comma-separated list of project directories (for `MODE=project`)
- `COMMON_PATH`: Optional path to a common libraries folder (for `MODE=project`)

### Repository Options

- `PRIVATE_REPOS`: `true`/`false` to create GitHub repos as private
- `DEFAULT_BRANCH`: Default branch for created repos (e.g., `main`, `master`)
- `REPO_NAME_TEMPLATE_APP`: Template for app repos (default `{name}-app`)
- `REPO_NAME_TEMPLATE_LIB`: Template for library repos (default `{name}-lib`)

### Advanced Detection (optional)

- `AUTO_DETECT`: Enable automatic project detection (`true`/`false`)
- `MANUAL_PROJECTS`: Comma-separated list of project paths (used when `AUTO_DETECT=false`)
- `MANUAL_COMMON_PATHS`: Comma-separated list of common component paths (used when `AUTO_DETECT=false`)
- `EXCLUDE_PATTERNS`: Comma-separated list of patterns to exclude from analysis
- `OPENAI_API_KEY`: OpenAI API key for enhanced AI analysis

### Example Configuration

```env
# Monorepo to split (SSH or HTTPS URL)
SOURCE_REPO_URL=git@github.com:mycompany/monorepo.git

# GitHub organization or username to create new repos under
ORG=mycompany

# GitHub Personal Access Token with repo scope
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Mode and Splitting Options
MODE=auto
# BRANCHES=frontend,backend,mobile
# PROJECTS=apps/web,apps/api,services/auth
# COMMON_PATH=shared

# Repository Options
PRIVATE_REPOS=false
DEFAULT_BRANCH=main
REPO_NAME_TEMPLATE_APP={name}-app
REPO_NAME_TEMPLATE_LIB={name}-lib

# Advanced Detection (optional)
AUTO_DETECT=true
# MANUAL_PROJECTS=app1,app2,services/api,frontend/web
# MANUAL_COMMON_PATHS=common,shared,libs
# EXCLUDE_PATTERNS=node_modules,.git,dist,build

# Optional: OpenAI API Key for enhanced AI analysis
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Usage

### Quick Start

1. **Test your configuration**:
   ```bash
   python test_config.py
   ```

2. **Analyze only (see what would be created)**:
   ```bash
   python split_repo_agent.py --mode auto --analyze-only
   ```

3. **Dry Run (Test Mode)**:
   ```bash
   # Auto mode (detect projects/components)
   python split_repo_agent.py --mode auto --dry-run
   
   # Project mode
   python split_repo_agent.py --mode project --projects apps/web,apps/api --common-path shared --dry-run
   
   # Branch mode
   python split_repo_agent.py --mode branch --branches main,api,mobile --dry-run
   ```

4. **Actual Execution**:
   ```bash
   # Auto mode
   python split_repo_agent.py --mode auto
   
   # Project mode
   python split_repo_agent.py --mode project --projects apps/web,apps/api --common-path shared
   
   # Branch mode
   python split_repo_agent.py --mode branch --branches main,api,mobile
   ```

### Programmatic Usage

You can also use the agent programmatically:

```python
from split_repo_agent import RepoSplitter, RepoSplitterConfig

config = RepoSplitterConfig(
    source_repo_url="git@github.com:org/monorepo.git",
    org="my-org",
    github_token="ghp_xxx",
    mode="auto",                  # or "project" | "branch"
    branches=["main", "api"],     # for branch mode
    manual_projects=["apps/web", "apps/api"],  # for project mode
    common_path="shared",         # optional common libs path
    private_repos=True,            # create private repos
    default_branch="main",        # default branch name
    repo_name_template_app="{name}-app",
    repo_name_template_lib="{name}-lib"
)

with RepoSplitter(config) as splitter:
    splitter.split_repositories()
```

### Example Output

#### Analysis Output
```
2024-01-15 10:30:00 - INFO - 🤖 Starting AI-powered monorepo analysis...
2024-01-15 10:30:01 - INFO - 🔍 Starting AI-powered monorepo analysis...
2024-01-15 10:30:02 - INFO - 📁 Detecting projects and applications...
2024-01-15 10:30:03 - INFO -   ✅ Detected nodejs project: frontend at apps/frontend
2024-01-15 10:30:03 - INFO -   ✅ Detected nodejs project: backend at apps/backend
2024-01-15 10:30:04 - INFO - 🔧 Detecting common components and shared libraries...
2024-01-15 10:30:04 - INFO -   ✅ Detected common component: utils at shared/utils
2024-01-15 10:30:05 - INFO - 🔗 Analyzing dependencies between projects...
2024-01-15 10:30:06 - INFO - 📊 Generating analysis report...
2024-01-15 10:30:06 - INFO - 📄 Analysis report saved to: monorepo_analysis.json
2024-01-15 10:30:06 - INFO - ============================================================
2024-01-15 10:30:06 - INFO - 📋 MONOREPO ANALYSIS SUMMARY
2024-01-15 10:30:06 - INFO - ============================================================
2024-01-15 10:30:06 - INFO - 🔍 Detected 2 projects:
2024-01-15 10:30:06 - INFO -   • frontend (nodejs) at apps/frontend
2024-01-15 10:30:06 - INFO -   • backend (nodejs) at apps/backend
2024-01-15 10:30:06 - INFO - 🔧 Detected 1 common components:
2024-01-15 10:30:06 - INFO -   • utils at shared/utils
2024-01-15 10:30:06 - INFO - 💡 Recommendations:
2024-01-15 10:30:06 - INFO -   • Split 2 detected projects into separate repositories
2024-01-15 10:30:06 - INFO -   • Extract 1 common components into shared libraries
```

#### Splitting Output
```
2024-01-15 10:35:00 - INFO - Processing project: frontend
2024-01-15 10:35:01 - INFO - Created repository: frontend-app
2024-01-15 10:35:05 - INFO - Successfully extracted project 'frontend' to 'frontend-app'
2024-01-15 10:35:05 - INFO - Repository URL: https://github.com/mycompany/frontend-app.git
2024-01-15 10:35:06 - INFO - Processing project: backend
2024-01-15 10:35:07 - INFO - Created repository: backend-app
2024-01-15 10:35:11 - INFO - Successfully extracted project 'backend' to 'backend-app'
2024-01-15 10:35:11 - INFO - Repository URL: https://github.com/mycompany/backend-app.git
2024-01-15 10:35:12 - INFO - Processing common component: utils
2024-01-15 10:35:13 - INFO - Created repository: utils-lib
2024-01-15 10:35:17 - INFO - Successfully extracted common component 'utils' to 'utils-lib'
2024-01-15 10:35:17 - INFO - Repository URL: https://github.com/mycompany/utils-lib.git
2024-01-15 10:35:18 - INFO - ============================================================
2024-01-15 10:35:18 - INFO - 🎉 REPOSITORY SPLITTING COMPLETED
2024-01-15 10:35:18 - INFO - ============================================================
2024-01-15 10:35:18 - INFO - Created 3 repositories:
2024-01-15 10:35:18 - INFO -   - frontend-app
2024-01-15 10:35:18 - INFO -   - backend-app
2024-01-15 10:35:18 - INFO -   - utils-lib
```

## How It Works

### 1. 🤖 AI-Powered Analysis
- **Project Detection**: Automatically identifies projects based on configuration files (package.json, requirements.txt, etc.)
- **Directory Structure Analysis**: Recognizes common patterns like `apps/`, `services/`, `frontend/`, `backend/`
- **Common Component Detection**: Identifies shared libraries, utilities, and components
- **Dependency Analysis**: Analyzes relationships between projects and components

### 2. 📁 Intelligent Project Recognition
The AI agent recognizes various project types:
- **Node.js**: package.json, next.config.js, vue.config.js, etc.
- **Python**: requirements.txt, setup.py, pyproject.toml
- **Java**: pom.xml, build.gradle
- **Go**: go.mod, go.sum
- **Rust**: Cargo.toml
- **PHP**: composer.json
- **Ruby**: Gemfile
- **Docker**: Dockerfile, docker-compose.yml
- **And more...**

### 3. 🔧 Repository Extraction
For each detected or configured unit (project/branch):
- Creates a new GitHub repository via API (respects privacy settings)
- Uses `git filter-repo` to extract only relevant files when needed
- Preserves complete git history for the extracted files
- Pushes to the new repository with the configured default branch

### 4. 📦 Common Component Extraction
For detected shared components:
- Creates separate library repositories
- Extracts common utilities, components, and shared code
- Maintains version history and dependencies
- Enables reuse across multiple projects

### 5. 📊 Analysis Reports
Generates comprehensive reports including:
- Detected projects and their types
- Common components and their usage
- Dependency relationships
- Recommendations for splitting strategy
- Analyzes file trees across all branches/projects
- Identifies common files that might be candidates for shared libraries
- Provides suggestions for what could be moved to `COMMON_PATH`

## Repository Structure

### After Branch Mode Splitting
```
mycompany/
├── frontend-app/     # Extracted from frontend branch
├── backend-app/      # Extracted from backend branch
├── mobile-app/       # Extracted from mobile branch
├── admin-app/        # Extracted from admin branch
├── api-app/          # Extracted from api branch
└── common-libs/      # Extracted from COMMON_PATH
```

### After Project Mode Splitting
```
mycompany/
├── fractol-app/      # Extracted from fractol/ directory
├── printf-app/       # Extracted from printf/ directory
├── pushswap-app/     # Extracted from pushswap/ directory
└── common-libs/      # Extracted from libft/ directory
```

## Project Structure

```
morethaneternity-project-main/
├── split_repo_agent.py    # Main agent script
├── test_config.py         # Configuration validation script
├── example_usage.py       # Programmatic usage example
├── force_update_repos.py  # Force update existing repositories
├── setup_project_mode.py  # Setup script for project mode
├── update_org_config.py   # Update organization configuration
├── env.example            # Example environment configuration
├── PROJECT_MODE_GUIDE.md  # Specific guide for project mode
├── debug_agent.py         # Debug utilities
├── run_agent.py           # Simple runner script
├── test_agent_direct.py   # Direct testing script
├── requirements.txt       # Python dependencies
├── .env                   # Configuration file (edit this)
├── .gitignore            # Git ignore rules
├── repo_splitter.log      # Log file (created during execution)
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

5. **Project Not Found (Project Mode)**
   - Ensure project directories exist in the repository
   - Check that `PROJECTS` variable contains valid directory names

6. **Repository Already Exists**
   - The agent will skip creation if repositories already exist
   - Use `force_update_repos.py` to update existing repositories with new content
   - Or delete existing repositories manually if you want to recreate them

7. **Virtual Environment Issues**
   - Always activate the virtual environment: `source venv/bin/activate`
   - If you get module errors, reinstall dependencies: `pip install -r requirements.txt`

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
3. **Test with `python split_repo_agent.py --dry-run --mode project`**
4. **Execute with `python split_repo_agent.py --mode project`**

The agent will create repositories based on your mode:
- **Auto Mode**: One repository per detected project + one per detected common component
- **Branch Mode**: One repository per branch
- **Project Mode**: One repository per project + optional common-libs

## Additional Tools

### Force Update Existing Repositories
If repositories already exist and you want to update them with new content:
```bash
python force_update_repos.py
```

### Setup Project Mode
Quick setup for project mode configuration:
```bash
python setup_project_mode.py
```

### Update Organization Configuration
Update the organization/username in your configuration:
```bash
python update_org_config.py
```

## Real-World Example

This agent was successfully used to split a monorepo with the following structure:
```
testmonorepo/
├── libft/           # Shared library
├── fractol/         # Project 1
├── printf/          # Project 2  
└── pushswap/        # Project 3
```

Into separate repositories:
```
Otazka/
├── fractol-app/      # Contains only fractol/ files with history
├── printf-app/       # Contains only printf/ files with history
├── pushswap-app/     # Contains only pushswap/ files with history
└── common-libs/      # Contains only libft/ files with history
```
