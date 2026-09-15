#!/usr/bin/env bash
# Deploy ./site to Cloudflare Workers static assets.
# Requires: npx on PATH, and either `npx wrangler login` done once,
# or CLOUDFLARE_API_TOKEN exported in your shell.
set -euo pipefail
cd "$(dirname "$0")"
exec npx --yes wrangler@latest deploy "$@"
