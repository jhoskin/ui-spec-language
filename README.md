# ui-spec-language

A text spec format that anchors a UI design without code or mockups, tested by rebuilding one app on a second stack from the spec alone.

The format and the process are defined in
[Text based UI design specs](docs/Text%20based%20UI%20design%20specs.md). A
small complete example is in
[Tessera worked example in consensus format](docs/Tessera%20worked%20example%20in%20consensus%20format.md).

The repository context is in [CONTEXT.md](CONTEXT.md). Decisions on points
that the report leaves open are in [DECISIONS.md](DECISIONS.md).

## Set up

```sh
just setup
```

This installs the one development dependency (Playwright, with install scripts
off) and downloads the Chromium build that it needs.

## Run the reference build

```sh
just serve
```

Then open <http://localhost:8000/web/>. Slate runs on the fixture in
`fixture/`. It has no back end, and a reload starts the data again.

## Check

```sh
just check
```
