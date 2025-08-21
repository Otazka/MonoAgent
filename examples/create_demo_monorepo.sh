#!/usr/bin/env bash
set -euo pipefail

DEMO_DIR="demo-monorepo"
rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"/apps/frontend/src "$DEMO_DIR"/apps/backend "$DEMO_DIR"/shared/utils

cat > "$DEMO_DIR/apps/frontend/package.json" <<'JSON'
{
  "name": "frontend",
  "version": "0.1.0",
  "dependencies": {"lodash": "^4.17.21"}
}
JSON

cat > "$DEMO_DIR/apps/frontend/src/index.js" <<'JS'
import _ from 'lodash';
console.log('frontend', _.chunk([1,2,3], 2));
JS

cat > "$DEMO_DIR/apps/backend/requirements.txt" <<'REQ'
flask==2.0.0
REQ

cat > "$DEMO_DIR/apps/backend/app.py" <<'PY'
print('backend ready')
PY

cat > "$DEMO_DIR/shared/utils/index.js" <<'JS'
export const hello = () => 'hello';
JS

pushd "$DEMO_DIR" >/dev/null
git init -q
git add .
git commit -qm "chore: initial demo monorepo"
popd >/dev/null

echo "Demo monorepo created at $DEMO_DIR"
echo "Try: export SOURCE_REPO_URL=$PWD/$DEMO_DIR && python split_repo_agent.py --analyze-only --dry-run"


