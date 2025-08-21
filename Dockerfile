# Syntax: docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib

# System deps: git, git-filter-repo, openssh-client for SSH auth, graphviz for visualization
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       git git-filter-repo openssh-client graphviz \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r monoagent && useradd -r -g monoagent monoagent

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Change ownership to non-root user
RUN chown -R monoagent:monoagent /app

# Create matplotlib config directory with proper permissions
RUN mkdir -p /tmp/matplotlib && chown monoagent:monoagent /tmp/matplotlib

# Switch to non-root user
USER monoagent

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python monitoring.py --health-check || exit 1

# Default command runs the splitter; can be overridden
CMD ["python", "split_repo_agent.py", "--analyze-only", "--dry-run"]


