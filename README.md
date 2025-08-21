# 🤖 GitHub Monorepo Splitter AI Agent

An intelligent AI-powered tool that automatically analyzes and splits GitHub monorepos into multiple repositories. This tool uses advanced pattern recognition and dependency analysis to intelligently separate projects, common components, and services.

## ✨ Features

- **🤖 AI-Powered Analysis**: Automatically detects projects, common components, and dependencies
- **🎯 Universal Splitting Modes**: 
  - `auto`: Intelligent automatic detection and splitting
  - `project`: Split specific projects with common components
  - `branch`: Split different branches into separate repositories
- **🔒 Security First**: Safe git operations, sanitized repository names, API retry logic
- **📊 Comprehensive Reporting**: Detailed analysis reports with recommendations
- **🛡️ Dry-Run Mode**: Preview changes before applying them
- **🎨 Customizable**: Configurable repository naming, privacy settings, and branch defaults
- **📈 Progress Tracking**: Real-time progress bars for all large operations
- **⚠️ Dependency Conflict Detection**: Advanced analysis to identify and resolve dependency conflicts
- **🤖 AI-Powered Analysis**: Intelligent recommendations for architecture, performance, and security
- **📊 Dependency Graph Visualization**: Beautiful visual representations of project relationships
- **🌐 Multi-Provider Support (beta)**: Create repositories on GitHub, GitLab, Bitbucket, Azure DevOps

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Git with `git-filter-repo` installed
- GitHub Personal Access Token with `repo` scope

### Installation

   ```bash
# Clone the repository
git clone https://github.com/yourusername/github-monorepo-splitter.git
cd github-monorepo-splitter

# Install dependencies
pip install -r requirements.txt

# Or install with pip
pip install github-monorepo-splitter
```

### Basic Usage

1. **Create configuration file**:
   ```bash
cp env.example .env
# Edit .env with your settings
   ```

2. **Run the splitter**:
   ```bash
# Auto mode (recommended)
python split_repo_agent.py --mode auto --dry-run

# Project mode
python split_repo_agent.py --mode project --projects app1,app2,app3 --common-path shared --dry-run

# Branch mode
python split_repo_agent.py --mode branch --branches main,develop,feature --dry-run
```

## 📋 Configuration

### Environment Variables (.env)

   ```bash
# Required
SOURCE_REPO_URL=git@github.com:org/monorepo.git
ORG=your-org-name
GITHUB_TOKEN=ghp_your_token_here

# Optional
MODE=auto                    # auto | project | branch
PRIVATE_REPOS=false          # Create private repositories
DEFAULT_BRANCH=main          # Default branch for new repos
REPO_NAME_TEMPLATE_APP={name}-app
REPO_NAME_TEMPLATE_LIB={name}-lib

# Project mode specific
PROJECTS=app1,app2,app3      # Comma-separated project names
COMMON_PATH=shared           # Common components path

# Branch mode specific
BRANCHES=main,develop,feature # Comma-separated branch names
```

### Command Line Options

   ```bash
python split_repo_agent.py [OPTIONS]

Options:
  --mode TEXT                 Splitting mode: auto, project, or branch
  --projects TEXT            Comma-separated list of projects (project mode)
  --branches TEXT            Comma-separated list of branches (branch mode)
  --common-path TEXT         Path to common components
  --private                  Create private repositories
  --default-branch TEXT      Default branch for new repositories
  --name-template-app TEXT   Template for app repository names
  --name-template-lib TEXT   Template for library repository names
  --dry-run                  Preview changes without applying
  --analyze-only             Only analyze, don't split
  --force                    Force proceed despite dependency conflicts
  --visualize                Generate dependency graph visualizations
  --provider TEXT            Target provider: github | gitlab | bitbucket | azure

### Usage Examples

   ```bash
# Basic analysis and splitting
python split_repo_agent.py --mode auto --dry-run

# Force proceed despite conflicts
python split_repo_agent.py --force

# Generate dependency graph visualizations
python split_repo_agent.py --visualize

# Analyze with AI recommendations and visualizations
python split_repo_agent.py --analyze-only --visualize

# Complete analysis with all features
python split_repo_agent.py --analyze-only --visualize --force
```

## 🔧 How It Works

### AI-Powered Analysis

The tool uses intelligent pattern recognition to:

1. **Detect Projects**: Identifies individual applications, services, and libraries
2. **Find Common Components**: Locates shared utilities, components, and libraries
3. **Analyze Dependencies**: Maps relationships between projects and components
4. **Generate Recommendations**: Suggests optimal splitting strategies

### Progress Tracking

The tool provides real-time progress bars for all major operations:

- **📁 File Scanning**: Shows progress while scanning repository files
- **🔍 Project Detection**: Tracks progress of project and component detection
- **🔗 Dependency Analysis**: Shows progress of dependency mapping
- **📝 Repository Creation**: Tracks GitHub API calls and repository creation
- **📦 Project Extraction**: Shows step-by-step progress of git operations
- **🌿 Branch Extraction**: Tracks branch-specific operations
- **🚀 Overall Progress**: Shows overall repository creation progress

### Dependency Conflict Detection

The tool intelligently detects and reports dependency conflicts:

- **🔴 Version Conflicts**: Identifies mismatched dependency versions across projects
- **🔴 Missing Dependencies**: Detects internal project dependencies that will be missing after splitting
- **🔴 Circular Dependencies**: Finds circular dependency chains between projects
- **🟡 Shared Dependencies**: Identifies dependencies used by multiple projects
- **💡 Resolution Suggestions**: Provides actionable recommendations for each conflict type
- **⚡ Force Mode**: Option to proceed despite conflicts using `--force` flag

### AI-Powered Analysis

The tool provides intelligent recommendations across multiple domains:

- **🏗️ Architecture Analysis**: Technology stack consolidation, component reusability, dependency optimization
- **⚡ Performance Analysis**: Large project identification, build optimization, deployment efficiency
- **🔒 Security Analysis**: Access control recommendations, repository security, team permissions
- **📊 Complexity Scoring**: Quantified complexity and readiness scores for informed decision-making
- **🎯 Priority Ranking**: Prioritized recommendations with impact and effort assessments

### Dependency Graph Visualization

Generate beautiful visual representations of your monorepo structure:

- **🎨 Multiple Formats**: PNG, SVG, and DOT file generation
- **🌈 Color-Coded Projects**: Different colors for different technology types
- **🔗 Dependency Relationships**: Clear visualization of project dependencies
- **⚠️ Conflict Highlighting**: Red edges for problematic dependencies
- **📊 Interactive Elements**: Legend and comprehensive labeling
- **🔄 Real-time Generation**: Automatic graph building during analysis

### Splitting Modes

#### Auto Mode
- Automatically detects all projects and common components
- Analyzes dependencies and usage patterns
- Creates separate repositories for each project
- Extracts common components into shared libraries

#### Project Mode
- Splits specific projects you define
- Extracts common components to shared repositories
- Maintains project-specific dependencies

#### Branch Mode
- Creates separate repositories for different branches
- Useful for feature-based development workflows
- Preserves branch-specific history and changes

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=split_repo_agent --cov-report=html

# Run specific test categories
python -m pytest tests/test_basic.py -v  # Basic functionality tests
python -m pytest tests/test_config.py -v  # Configuration tests
python -m pytest tests/test_utils.py -v   # Utility function tests
```

### Test Coverage

- **Unit Tests**: Core functionality, configuration, utilities
- **Integration Tests**: End-to-end workflows
- **Mock Tests**: External API interactions
- **Coverage**: >80% code coverage with detailed reports

## 🔄 CI/CD Pipeline

The project includes GitHub Actions workflows for:

- **Automated Testing**: Multi-Python version testing (3.9-3.12)
- **Code Quality**: Linting with flake8, black, and isort
- **Security**: Bandit and safety checks
- **Coverage**: Automated coverage reporting
- **Build**: Package building and artifact creation

## 📊 Example Output

```
🔍 Starting AI-powered monorepo analysis...
📁 Scanning files: 100%|██████████| 1500/1500 [00:02<00:00, 750.00 files/s]
🔍 Grouping files by directory: 100%|██████████| 1500/1500 [00:01<00:00, 1500.00 files/s]
🎯 Detecting projects: 100%|██████████| 50/50 [00:03<00:00, 16.67 dirs/s]
🏗️  Analyzing directory structure: 100%|██████████| 1500/1500 [00:05<00:00, 300.00 files/s]
🔧 Detecting common components: 100%|██████████| 1500/1500 [00:02<00:00, 750.00 files/s]
🔗 Analyzing dependencies: 100%|██████████| 200/200 [00:10<00:00, 20.00 files/s]
⚠️  Detecting dependency conflicts: 100%|██████████| 200/200 [00:05<00:00, 40.00 files/s]
📊 Generating analysis report...

📋 MONOREPO ANALYSIS SUMMARY
============================================================
🔍 Detected 2 projects:
  • frontend (nodejs) at apps/frontend
  • backend (python) at apps/backend
🔧 Detected 1 common components:
  • utils at shared/utils
⚠️  Detected 3 dependency conflicts:
  🔴 VERSION_MISMATCH: Version conflict for 'react': {'frontend': '^18.0.0', 'backend': '^17.0.0'}
    💡 Standardize 'react' version across all projects
    💡 Move 'react' to a shared dependency management system
  🔴 MISSING_DEPENDENCY: Project 'frontend' depends on project 'backend' which will be separated
    💡 Move shared code from 'backend' to a common component
    💡 Create a shared library for 'backend'
  🟡 SHARED_DEPENDENCY: 'lodash' is used by 2 projects: frontend, backend
    💡 Consider creating a shared library for 'lodash'
    💡 Move 'lodash' to a common component

🤖 AI-POWERED ANALYSIS
============================================================
📊 Complexity Score: 45/100
📊 Readiness Score: 75/100
🚨 2 High-Priority Recommendations:
  🔴 [10] Dependency Conflict Resolution
    📝 Resolve 2 critical dependency conflicts before splitting
    💡 Benefit: Prevent build failures and runtime issues in separated repositories
  🟠 [8] Technology Stack Consolidation
    📝 Consider consolidating from 2 different technologies to reduce complexity
    💡 Benefit: Reduced maintenance overhead and improved developer productivity
📊 Visualizations Generated:
  • PNG: dependency_graph.png
  • DOT: dependency_graph.dot
  • SVG: dependency_graph.svg

💡 Recommendations:
  • Split 2 detected projects into separate repositories
  • Extract 1 common components into shared libraries
  ⚠️  Resolve 2 critical dependency conflicts before splitting
  ⚠️  Address 1 high-severity dependency conflicts

🚀 Creating repositories: 100%|██████████| 3/3 [01:30<00:00, 30.00s/repo]
📝 Creating frontend-app: 100%|██████████| 1/1 [00:05<00:00, 5.00s/attempt]
📦 Extracting frontend: 100%|██████████| 7/7 [00:45<00:00, 6.43s/step]
📝 Creating backend-app: 100%|██████████| 1/1 [00:03<00:00, 3.00s/attempt]
📦 Extracting backend: 100%|██████████| 7/7 [00:38<00:00, 5.43s/step]
📝 Creating utils-lib: 100%|██████████| 1/1 [00:02<00:00, 2.00s/attempt]
🔧 Extracting utils: 100%|██████████| 7/7 [00:25<00:00, 3.57s/step]
✅ Successfully split monorepo into 3 repositories!
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/ -v

# Run linting
flake8 split_repo_agent.py
black split_repo_agent.py
isort split_repo_agent.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ for the open-source community
- Inspired by the challenges of managing large monorepos
- Powered by GitHub's powerful API and git-filter-repo

## 📞 Support

- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/github-monorepo-splitter/issues)
- 📖 Documentation: [Project Wiki](https://github.com/yourusername/github-monorepo-splitter/wiki)

---

**Made with 🤖 AI and ❤️ by Elena Surovtseva**
