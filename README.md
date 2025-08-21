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
```

## 🔧 How It Works

### AI-Powered Analysis

The tool uses intelligent pattern recognition to:

1. **Detect Projects**: Identifies individual applications, services, and libraries
2. **Find Common Components**: Locates shared utilities, components, and libraries
3. **Analyze Dependencies**: Maps relationships between projects and components
4. **Generate Recommendations**: Suggests optimal splitting strategies

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
📁 Detecting projects and applications...
  ✅ Detected nodejs project: frontend at apps/frontend
  ✅ Detected python project: backend at apps/backend
🔧 Detecting common components and shared libraries...
  ✅ Detected common component: utils at shared/utils
🔗 Analyzing dependencies between projects...
📊 Generating analysis report...

📋 MONOREPO ANALYSIS SUMMARY
============================================================
🔍 Detected 2 projects:
  • frontend (nodejs) at apps/frontend
  • backend (python) at apps/backend
🔧 Detected 1 common components:
  • utils at shared/utils
💡 Recommendations:
  • Split 2 detected projects into separate repositories
  • Extract 1 common components into shared libraries

🚀 Starting repository splitting...
✅ Created repository: frontend-app
✅ Created repository: backend-app
✅ Created repository: utils-lib
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
