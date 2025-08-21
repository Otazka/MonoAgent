from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="github-monorepo-splitter",
    version="1.0.0",
    author="Elena Surovtseva",
    author_email="your.email@example.com",
    description="AI-powered GitHub monorepo splitter with intelligent project detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/github-monorepo-splitter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "monorepo-splitter=split_repo_agent:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="monorepo, git, github, repository, split, ai, automation",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/github-monorepo-splitter/issues",
        "Source": "https://github.com/yourusername/github-monorepo-splitter",
        "Documentation": "https://github.com/yourusername/github-monorepo-splitter#readme",
    },
)
