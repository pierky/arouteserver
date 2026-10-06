# ARouteServer — notes for AI agents

## What this project is

ARouteServer is a Python CLI tool that generates (and tests) configuration
files for BGP route servers (currently BIRD 1.6.x, BIRD 2.x, BIRD 3.x, and
OpenBGPD/OpenBGPD Portable) from two YAML input files
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
  - `commands/` — CLI subcommands. The entry point is `cli.py`
    (`main()`), installed as the `arouteserver` console script;
    `scripts/arouteserver` is a thin wrapper around it, to run the program
    from a checkout with `PYTHONPATH` set to the repo root.
  - `pierky/` itself is a PEP 420 namespace package: it has no
    `__init__.py`, don't add one.
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
  through a throwaway BIRD/OpenBGPD container), `utils/test_docker_images`
  (runs locally the "docker-image-tests" job of `cicd.yml` for each entry of
  its matrix; also run by `utils/update_tests`).
- `tools/playground` — a separate Docker-based sandbox to experiment with
  a full virtual IXP.
- `.github/workflows/cicd.yml` — canonical reference for how tests are run
  in CI, which Docker images are expected, and which Python versions are
  officially supported. `test_latest_deps.yml` runs weekly against the
  newest dependency releases allowed by `pyproject.toml`.
- `pyproject.toml` — all the package metadata and build config (setuptools
  backend; `setup.py` is only a compatibility stub), runtime dependencies,
  and the `dev`/`docs` dependency groups. `uv.lock` pins the exact
  versions used by CI, the Docker image and Read the Docs: after changing
  dependencies in `pyproject.toml`, run `uv lock` and commit both files
  (CI uses `uv sync --locked`, which fails if they're out of sync).
- `RELEASING.rst` — the maintainer's release checklist.

## Running tests

The dev environment is defined by `pyproject.toml` + `uv.lock`: `uv sync`
creates (or updates) `.venv` with exactly the locked runtime and `dev`
dependencies, plus the package itself in editable mode. Note that `uv sync`
also removes from `.venv` whatever isn't in the lock file.

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
3. The container images the scenarios reference: `pierky/bird:1.6.8` (used
   as the generic client/peer simulator in *every* scenario, regardless of
   which BIRD version the route server itself targets — see the "BGP
   speaker versions" section below), `pierky/bird:2.19.2`,
   `pierky/bird:3.2.3`, `pierky/bird:3.3.2` for the route-server side, plus
   `pierky/openbgpd:9.2`/`9.3` for the OpenBGPD route-server side — see
   `.github/workflows/cicd.yml` for the full list CI pulls. Check with
   `docker images`; pull from Docker Hub or build from
   `github.com/pierky/dockerfiles` (see `docs/LIVETESTS.rst`) if missing.

Run a single scenario file:

```bash
source .venv/bin/activate
python -m pytest tests/live_tests/scenarios/default/test_bird2_4.py
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

## BGP speaker versions (adding/bumping a target release)

Version support has two independent halves — both need updating together
when bumping a version, but neither implies the other:

1. **What the CLI can render for** ("target support"):
   `BIRDConfigBuilder.AVAILABLE_VERSION`/`DEFAULT_VERSION` and
   `OpenBGPDConfigBuilder.AVAILABLE_VERSION`/`DEFAULT_VERSION` in
   `pierky/arouteserver/builder.py`. These drive the `--target-version`
   CLI choices/default (`commands/configure.py`, `commands/tpl_rendering.py`).
   Templates gate version-specific behaviour via the Jinja filters
   `target_version_ge`/`_le`/`_lt` (defined in `builder.py`, backed by
   `packaging.version`) — range comparisons, not exact-match, so a new
   patch/minor release usually renders correctly with zero template
   changes unless the daemon itself changed syntax (see below).
2. **What the live-tests suite actually exercises**: one class per tested
   release in `pierky/arouteserver/tests/live_tests/bird.py`
   (`BIRD2Instance`, `BIRD32Instance`, `BIRD33Instance`, …, each pinning
   `DOCKER_IMAGE`/`TAG`/`TARGET_VERSION`) and `openbgpd.py` (same pattern,
   one class per exact OpenBGPD release). `TAG` must be unique per class —
   it names the per-instance rendered-config/route-dump files
   (`LiveScenario.get_instance_tag()` in `tests/live_tests/base.py`).
   Scenario test files (`tests/live_tests/scenarios/*/test_bird*.py`) only
   ever set `RS_INSTANCE_CLASS` (+ `SHORT_DESCR`) to one of these classes —
   the shared scenario logic in each dir's `base.py` is version-agnostic
   and does not need touching for a version bump.

**Gotcha**: `BIRDInstance`/`BIRDInstanceIPv4`/`BIRDInstanceIPv6` (the base
class, pinned at `pierky/bird:1.6.8`) are reused everywhere as the generic
"dumb" client/peer simulator (AS1/AS2/etc.), even inside BIRD2/BIRD3-target
scenarios. Don't touch these, and don't drop `pierky/bird:1.6.8` from
CI/tooling pulls, when retiring or changing a *route-server* target — it's
unrelated infrastructure. As of the BIRD 2.19.2/3.2.3/3.3.2 update, BIRD
1.x live-test *scenarios* (`test_bird1_*.py`) were removed for CI-cost
reasons, but BIRD 1.x remains a valid `--target-version`.

Live-test files for a tested BIRD3.x line are named `test_bird3<minor>_*.py`
(e.g. `test_bird32_4.py`, `test_bird33_6.py`) — no dots, mirroring the
pre-existing `test_bird2_*.py` convention.

Sanity-check a template change against a real daemon without the full
live-tests framework: render with the CLI
(`./scripts/arouteserver bird --cfg var/arouteserver.yml --target-version
X.Y.Z ... -o /path/to/bird.conf`) then
`docker run --rm -v /path/to/bird.conf:/etc/bird/bird.conf pierky/bird:X.Y.Z bird -c /etc/bird/bird.conf -d -p`
(`-p` = parse-only, no daemon start). 

### Procedure: adding a new release of a supported BGP speaker

Reference commits: 613c94ec (BIRD 2.16 + OpenBGPD 8.7, the minimal
case), 4ff763c6 (OpenBGPD 9.2), 222efd6d (BIRD 2.19.2/3.2.3/3.3.2, with
template changes and a new BIRD 3.x line). Steps, in order:

1. **Docker image.** `pierky/bird:<ver>` / `pierky/openbgpd:<ver>` must be
   published on Docker Hub (built from `github.com/pierky/dockerfiles`):
   CI pulls it from there, it is never built by this repo.
2. **Read the upstream release notes** for config-syntax changes, removed
   keywords, or changed defaults. If something affects the rendered
   config, gate it with `"X.Y"|target_version_ge` (or `_le`/`_lt`) in
   `templates/<daemon>/*.j2`, and/or add a compatibility check in the
   builder's `validate_bgpspeaker_specific_configuration()`, keeping the
   output for older targets byte-identical. After *any* template edit run
   `python utils/update_fingerprints.py` (from the repo root) and commit
   `templates/fingerprints.yml` (`tests/static/test_cfg_program.py` fails
   otherwise). Often nothing needs changing here.
3. **Target support** (`pierky/arouteserver/builder.py`): append the
   version to `AVAILABLE_VERSION`, keeping the list ordered oldest → newest.
   - OpenBGPD: `DEFAULT_VERSION = AVAILABLE_VERSION[-1]`, so the newest
     entry automatically becomes the default (also for `configure`).
   - BIRD: `DEFAULT_VERSION` is explicit; change it only if the new
     release should become the default. Several tools derive "latest"
     from the list: the newest `2.*`/`3.*` entries (`tests/cli`,
     `utils/build_doc`) and `AVAILABLE_VERSION[-1]` (the "latest BIRD"
     step of the docker-image tests).
4. **Live-test instance classes**
   (`pierky/arouteserver/tests/live_tests/{bird,openbgpd}.py`):
   - OpenBGPD: add `OpenBGPD<XY>PortableInstance` (`DOCKER_IMAGE`, unique
     `TAG = "openbgpd<XY>p"`, `BGP_SPEAKER_VERSION`, `TARGET_VERSION`), then
     shift the aliases: `OpenBGPDPortablePreviousInstance` becomes the old
     latest, `OpenBGPDPortableLatestInstance` the new class. Scenario files
     only reference the aliases (`Previous` is used by the `global`
     scenario only), so no scenario edits are needed. Old classes are
     kept.
   - BIRD, newer release of an already-tested line: bump `DOCKER_IMAGE`/
     `TARGET_VERSION` of the existing class (e.g. `BIRD2Instance`) and keep
     its `TAG`.
   - BIRD, new release line: add a new class with a new `TAG`, add
     `test_bird3<minor>_*.py` files to each scenario directory, and add the
     speaker id to `ALL_BGPSPEAKERS` in `utils/update_tests`.
   - Never touch the `pierky/bird:1.6.8`-based client classes (see the
     gotcha above).
5. **Images pulled for the tests**: add the new image and drop any image
   no longer used by a tested class, in all three places, kept in sync:
   the "Fetch Docker images used by tests" step of
   `.github/workflows/cicd.yml`, `utils/update_tests`, and the setup
   section of `docs/LIVETESTS.rst`.
6. **Hard-coded versions elsewhere**: the docker-image-tests job of
   `.github/workflows/cicd.yml` (OpenBGPD `VERSION=` and validation image;
   the per-line BIRD 3.x steps and the custom-`general.yml` BIRD step) and
   its local mirror `utils/test_docker_images`, plus `utils/test_config`.
   `git grep` for the old version string to catch them all.
7. **Docs**: add a `CHANGES.rst` entry to the topmost (unreleased)
   section, e.g. "New: add support for `<Daemon> <ver> <release-notes
   URL>`__, which also becomes the new default version for
   <Daemon>-based configurations, also added to the integration testing
   suite." Update `docs/FEATURES.rst` only if the supported-versions
   sentence changes (e.g. a new major line), and the image versions
   mentioned in this file.
8. **Verify**: static tests; `bash tests/cli` (it renders and validates
   with the real daemon for the latest OpenBGPD and BIRD v2 targets); a
   render + parse-only check for the new target (see above; for OpenBGPD
   use `bgpd -f /etc/bgpd/bgpd.conf -d -n`); a `BUILD_ONLY=1` pass over
   the speaker's scenario files; then the full live tests for that speaker
   (e.g. `tests/live_tests/scenarios/*/test_openbgpd_portable*.py`), one
   scenario directory at a time. The live tests dump the rendered config
   and the routes into `configs/<ScenarioClass>/<TAG>.conf` and
   `routes/<ScenarioClass>/<TAG>/*.txt` inside each scenario directory:
   the new `<TAG>` dumps are committed together with the change; dumps
   for older tags are left in place.
9. **Follow-up (separate "Update tests and docs" commit)**:
   `utils/update_tests` regenerates `tests/last` and
   `docs/SUPPORTED_SPEAKERS_CI.txt`; `utils/build_doc` regenerates
   `README.rst`, `docs/EXAMPLES.rst` and `examples/*` (see the next
   section). Both need `SECRET_PEERINGDB_API_KEY`; never hand-edit
   their outputs.

## Doc/example regeneration (`utils/build_doc`)

`README.rst`, `docs/EXAMPLES.rst`, `docs/SUPPORTED_SPEAKERS_CI.txt`/
`SUPPORTED_SPEAKERS_FEATURES.txt`, and the `examples/*` configs are all
auto-generated by `utils/build_doc` — never hand-edit them directly.
`README.rst` itself is a concatenation of `docs/README_header.txt` +
`docs/FEATURES.rst` + `docs/README_fulldocs.txt` + `docs/STATUS.txt` +
`docs/README_footer.txt`, so prose changes (e.g. the supported-BIRD-versions
sentence) belong in `docs/FEATURES.rst`, not `README.rst`.

Requirements to actually run it:
- `SECRET_PEERINGDB_API_KEY` env var (a real PeeringDB API key — it hits
  live PeeringDB/RIPE-RPKI services).
- `var/build_doc.yml` (a program config file — `var/` is gitignored; if
  missing, copy `var/arouteserver.yml` if one already exists, or generate
  one with `arouteserver setup`).
- It ends with two interactive `[yes/NO]` prompts (Euro-IX/IX-F export) —
  safe to answer "no" for a routine doc regen.
- The very last step validates the PyPI long description by building the
  package (`uv build`) and running `uvx twine check --strict` on it, so it
  needs `uv` on `PATH`. A failure there aborts the script (via `set -e`)
  *after* all the doc/example files are already regenerated.
- `BIRDConfigBuilder.AVAILABLE_VERSION`'s newest `"2.*"` entry drives the
  example BIRD v2 config/CLI transcript automatically
  (`BIRD2_LATEST_VERSION` in the script); there is deliberately no BIRD v3
  example-rendering step today.
- Bumping the default BIRD version regenerates the `never_via_route_servers`
  ASN list examples with a large, unrelated-looking diff — that's just
  live PeeringDB data drift, not a regression.

## Local Environment

If `AGENTS.local.md` exists in the project root, read it for local environment variables, workstation-specific paths, or local dev setup.