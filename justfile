# One command runs every gate: `just check`.

default: check

# Install the pinned development dependency and its browser.
setup:
    npm ci --ignore-scripts --no-audit --no-fund
    npx playwright install chromium-headless-shell

# Markdown lint, default rules, line length off.
lint-md:
    markdownlint-cli2

# JavaScript lint and format check.
lint-js:
    deno lint web tools
    deno fmt --check web tools

# Unit tests.
test:
    node --test

check: lint-md
