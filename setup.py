from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="monoagent",
    version="1.0.0",
    author="Elena Surovtseva",
    author_email="your.email@example.com",
    description="AI-powered monorepo splitter with intelligent project detection and multi-provider support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Otazka/MonoAgent",
    packages=find_packages(),
    # Ensure single-module entry point is included
    py_modules=["split_repo_agent"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
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
            "monoagent=split_repo_agent:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="monorepo, git, github, gitlab, bitbucket, azure, repository, split, ai, automation",
    project_urls={
        "Bug Reports": "https://github.com/Otazka/MonoAgent/issues",
        "Source": "https://github.com/Otazka/MonoAgent",
        "Documentation": "https://github.com/Otazka/MonoAgent#readme",
    },
)
