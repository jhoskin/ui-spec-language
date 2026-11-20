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
    deno lint
    deno fmt --check

# Unit tests, service double vectors and browser tests of the reference build.
test:
    node --test web/test

# Serve the reference build for a person, with real time.
serve:
    python3 -m http.server 8000

check: lint-md lint-js test
