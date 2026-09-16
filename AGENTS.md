# ARouteServer — notes for AI agents

## What this project is

ARouteServer is a Python CLI tool that generates (and tests) configuration
files for BGP route servers (currently BIRD 1.6.x, BIRD 2.x, BIRD 3.x
pre-release, and OpenBGPD/OpenBGPD Portable) from two YAML input files
(`general.yml` for policies, `clients.yml` for the route server's clients).
It enriches that input with data pulled from IRRDBs (via `bgpq3`/`bgpq4`),
PeeringDB, RPKI ROAs/RTR, etc., then renders the final config through Jinja2
templates. Correctness is validated with an integration-test framework
("live tests") that spins up real BIRD/OpenBGPD instances in Docker
containers and checks the resulting BGP sessions/routes.

Read `README.rst` and `docs/` (Sphinx sources) for the full user-facing
picture; `docs/LIVETESTS.rst` and `docs/LIVETESTS_CODEDOC.rst` specifically
document the live-tests framework in detail.

## Repository layout

- `pierky/arouteserver/` — the actual Python package.
  - `builder.py`, `config/`, `enrichers/` — config parsing and the
    IRRDB/PeeringDB/RPKI enrichment pipeline.
  - `templates/` — Jinja2 templates that render BIRD/OpenBGPD configs.
  - `commands/` — CLI subcommands (entry point is `scripts/arouteserver`).
  - `tests/` — **the actual test suites live inside the package**, not at
    the repo root (`tests/` at the repo root mostly symlinks/mirrors into
    here — see below).
- `tests/` (repo root) — pytest is normally invoked against paths under
  here; scenario directories under `tests/live_tests/scenarios/*` contain
  symlinks (`bird -> ../../../../templates/bird`, `general.yml -> ...`,
  etc.) back into `pierky/arouteserver/tests/live_tests/...` and
  `config.d/`, plus scenario-specific `base.py`/`test_*.py`/templates.
  - `static/` — plain unittest/pytest modules, no containers needed, fast.
  - `live_tests/` — Docker-based integration tests (see below).
  - `real/` — scenarios built from real IXPs' member lists.
  - `external_resources/` — tests that hit real external services
    (PeeringDB, RIPE RPKI cache, bgpq3/4); scheduled separately in CI.
  - `cli/` — shell-based CLI smoke tests.
- `config.d/` — example/base `general.yml`, `clients.yml`, `bogons.yml`
  used as building blocks by live-test scenarios (symlinked in).
- `docker/` — Dockerfile for the published `pierky/arouteserver` image.
- `utils/` — dev helper scripts: `utils/run <instance> <cmd>` (exec into a
  running live-test container by its short name, e.g. `rs`, `AS1`),
  `utils/birdcl`/`utils/birdcl6` (wrap `birdcl` inside a container),
  `utils/docker_stopall` (force-remove all `ars_*` containers),
  `utils/build_doc` (regenerates `README.rst` — it's auto-generated, do
  not hand-edit it), `utils/test_config` (run a standalone config file
  through a throwaway BIRD/OpenBGPD container).
- `tools/playground` — a separate Docker-based sandbox to experiment with
  a full virtual IXP.
- `.github/workflows/cicd.yml` — canonical reference for how tests are run
  in CI, which Docker images are expected, and which Python versions are
  officially supported.

## Running tests

### Static tests (no containers, fast, always safe to run)

```bash
source .venv/bin/activate
python -m pytest tests/static/
```

### Live tests (Docker integration tests)

These start real BIRD/OpenBGPD containers, wire them into a Docker
bridge network, and check BGP sessions/routes.

Prerequisites (normally one-time setup per machine — check before assuming
they're missing, they may already be in place):

1. A container engine reachable as `docker` on `PATH`.
2. A bridge network named `arouteserver` on `192.0.2.0/24` /
   `2001:db8:1:1::/64`. The test framework creates this automatically on
   first run (`DockerInstance._setup_networking()` in
   `pierky/arouteserver/tests/live_tests/docker.py`) — you normally don't
   need to create it by hand. Check with `docker network ls` /
   `docker network inspect arouteserver`.
3. The container images the scenarios reference, at minimum
   `pierky/bird:1.6.8` for the built-in BIRD 1 scenarios (also
   `pierky/bird:2.16`, `pierky/bird:3.0-alpha2`,
   `pierky/openbgpd:8.4`/`8.7` etc. for the other speaker versions — see
   `.github/workflows/cicd.yml` for the full list CI pulls). Check with
   `docker images`; pull from Docker Hub or build from
   `github.com/pierky/dockerfiles` (see `docs/LIVETESTS.rst`) if missing.

Run a single scenario file:

```bash
source .venv/bin/activate
python -m pytest tests/live_tests/scenarios/default/test_bird1_4.py
```

Or the whole live-tests suite: `pytest tests/live_tests/`.

Useful environment variables (see `docs/LIVETESTS.rst` for more):

- `BUILD_ONLY=1` — only render configs, don't start containers or run
  assertions. Good smoke test that doesn't need a working container engine.
- `REUSE_INSTANCES=1` — leave containers running after the test for manual
  poking instead of tearing them down. Only reuse across runs of the *same*
  scenario.
- `DEBUG=1` — verbose debug output from the test framework.
- `ARS_LIVE_TESTS_VAR_DIR` — redirects where rendered per-scenario config files (the ones
  bind-mounted into containers) are written, for environments where the
  repo's own path isn't visible to the container engine.

Debugging a running scenario (needs `REUSE_INSTANCES=1`):

```bash
docker ps                          # list ars_* containers
./utils/run rs birdcl show route   # exec a command in the "rs" instance
./utils/birdcl rs show route       # shortcut for the above
./utils/docker_stopall             # force-remove all ars_* containers
```

### Container/network hygiene

Live-test containers are started with `--rm`, so a clean pytest exit (or
Ctrl-C reaching the teardown code) leaves nothing running. If a run is
killed hard, stray `ars_*` containers can linger — check with `docker ps -a`
and clean up with `./utils/docker_stopall` before re-running. Don't
remove the `arouteserver` Docker network unless it's actually
misconfigured (wrong subnet) — the framework reuses it across runs and
recreating it is a shared, semi-persistent piece of local test
infrastructure, not per-run state.

### Don't run live tests concurrently

The framework uses fixed container names (`ars_<instance>`) and fixed IPs
on the shared `arouteserver` network, so two `pytest tests/live_tests/...`
invocations running at the same time (e.g. one from an agent, one from a
developer in another terminal) will collide and produce confusing,
flaky-looking failures — containers from one run getting stopped/renamed
out from under the other, "instance is not running" errors on scenarios
that never touched, etc. Before starting a live-test run, check `docker ps -a`
for containers you didn't start; if something unrelated is already
running, wait rather than launching another suite in parallel. 

## Local Environment

If `AGENTS.local.md` exists in the project root, read it for local environment variables, workstation-specific paths, or local dev setup.