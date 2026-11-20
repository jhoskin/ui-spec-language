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

# Unit tests, service double vectors and browser tests of the reference build, and tool tests.
test:
    node --test web/test tools/test

# Serve the reference build for a person, with real time.
serve:
    python3 -m http.server 8000

# The trigger lint of the specification package.
spec-lint:
    node tools/lint.mjs

# Public scenarios and the closure check on the web build.
scenarios-web:
    node tools/run.mjs --build web --quiet --out out/results-web.json
    node tools/closure.mjs --build web

# Generate trace.md from the results of the builds.
trace:
    node tools/trace.mjs

check: lint-md lint-js test spec-lint scenarios-web trace
