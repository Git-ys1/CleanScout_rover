#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
current_dir="$(pwd)"

if [[ "${current_dir}" != "${repo_root}" ]]; then
  echo "Run this script from the repo root. Current directory: ${current_dir}" >&2
  exit 1
fi

if [[ ! -f "${repo_root}/package.json" ]]; then
  echo "package.json was not found. Current directory is not a valid vue3 repo root." >&2
  exit 1
fi

if ! grep -q '"build:mp-weixin:production"' "${repo_root}/package.json"; then
  echo "build:mp-weixin:production is not defined in package.json." >&2
  exit 1
fi

echo "Running mini program build: npm run build:mp-weixin:production"
npm run build:mp-weixin:production

artifact_dir="${repo_root}/dist/build/mp-weixin"
project_config="${artifact_dir}/project.config.json"

if [[ ! -f "${project_config}" ]]; then
  echo "project.config.json was not generated." >&2
  exit 1
fi

appid="$(node -e "const fs=require('fs'); const c=JSON.parse(fs.readFileSync(process.argv[1], 'utf8')); process.stdout.write(String(c.appid || ''))" "${project_config}")"

if [[ "${appid}" != "wxce1a2e91132f4c41" ]]; then
  echo "Unexpected mp-weixin appid: ${appid}. Expected wxce1a2e91132f4c41." >&2
  exit 1
fi

echo
echo "Mini program build finished."
echo "Artifact directory: ${artifact_dir}"
echo "AppID: ${appid}"
echo "Next step: import that dist/build/mp-weixin directory into WeChat DevTools."
