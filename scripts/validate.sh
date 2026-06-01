#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python - <<'PY'
import json, pathlib, py_compile, re, subprocess, sys, yaml
root = pathlib.Path('.')
yaml.safe_load((root/'docker-compose.yml').read_text(encoding='utf-8'))
json.load(open(root/'html/labHero_efects.json', encoding='utf-8'))
py_compile.compile(str(root/'uploader/app.py'), doraise=True)
py_compile.compile(str(root/'video-optimizer-backend/main.py'), doraise=True)
html = (root/'html/index.html').read_text(encoding='utf-8')
scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
(root/'.tmp_validate_labhero.js').write_text('\n;\n'.join(scripts), encoding='utf-8')
print('YAML, JSON y Python OK.')
PY

if command -v node >/dev/null 2>&1; then
  node --check .tmp_validate_labhero.js
  echo "JavaScript OK."
else
  echo "Node no está instalado; omitida validación JS."
fi
rm -f .tmp_validate_labhero.js
