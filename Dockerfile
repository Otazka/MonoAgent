# Syntax: docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps: git, git-filter-repo, openssh-client for SSH auth, graphviz for visualization
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git git-filter-repo openssh-client graphviz \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Default entrypoint runs the splitter; pass flags via `docker run ... -- <flags>` or override CMD
ENTRYPOINT ["python", "split_repo_agent.py"]
CMD ["--analyze-only", "--dry-run"]


