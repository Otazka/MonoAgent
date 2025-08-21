# Examples

This folder contains example workflows to help you try the splitter quickly.

## Option A: Use a public demo monorepo (recommended)

If you have a public monorepo, set the variables and run analyze:

```bash
# In project root
cp env.example .env
# Edit .env:
#  SOURCE_REPO_URL=git@github.com:yourorg/your-monorepo.git (or HTTPS URL)
#  ORG=yourorg
#  GITHUB_TOKEN=ghp_xxx

python split_repo_agent.py --preflight
python split_repo_agent.py --analyze-only --dry-run
python split_repo_agent.py --mode auto
```

If you want to try with a sample public demo (replace with your own or any public monorepo):

```bash
export SOURCE_REPO_URL=https://github.com/vercel/next.js
export ORG=yourorg
export GITHUB_TOKEN=ghp_xxx
python split_repo_agent.py --analyze-only --dry-run
```

> Note: Selecting a monorepo with obvious app folders (apps/*, packages/*, etc.) yields better demos.

## Option B: Generate a local demo monorepo

Use the helper script to generate a small monorepo locally, with commits and a shared folder. This does not require network access.

```bash
bash examples/create_demo_monorepo.sh
# Follow the on-screen instructions to analyze/split the generated repo
```

What the script creates:
- apps/frontend (JS)
- apps/backend (Python)
- shared/utils (JS)

It simulates history and content to let the analyzer detect projects and dependencies.

---

## Reproduction script (CI friendly)

For automated demos (e.g., in CI), capture a progress file and JSON logs:

```bash
LOG_JSON=true PROGRESS_FILE=progress.jsonl \
python split_repo_agent.py --mode auto --analyze-only --dry-run
cat progress.jsonl
```

Then run the split against your test org (requires token and permissions):

```bash
python split_repo_agent.py --mode auto
```

> To limit repository creation during demos, set `--dry-run` or point to a throwaway org.
