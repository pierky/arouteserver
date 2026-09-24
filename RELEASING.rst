Release procedure
=================

Maintainer checklist for publishing a new release of ARouteServer.

The commands below are run from the root of the repository and assume
that `uv <https://docs.astral.sh/uv/>`__ is installed.

Preparation
-----------

1. Update the fingerprints and run the whole test suite, including the live
   tests:

   .. code:: bash

      ./utils/update_fingerprints.py
      ./utils/update_tests

2. Set the new version in ``pierky/arouteserver/version.py``:

   - dev releases: ``X.YY.Z-alpha1``, ``X.YY.Z-alpha2``, ...
   - production releases: ``X.YY.Z``

   ``pyproject.toml`` reads the version from there, and ``uv.lock`` does
   not contain it: there is no need to update anything else.

3. Update ``CHANGES.rst``.

4. If the supported Python versions changed, keep ``requires-python`` and
   the classifiers in ``pyproject.toml`` in sync with the matrix in
   ``.github/workflows/cicd.yml`` (and in ``test_latest_deps.yml``).

5. Verify that ``uv.lock`` is in sync with ``pyproject.toml``:

   .. code:: bash

      uv lock --check

6. Build the distribution files (sdist and wheel) and check them: the
   long description is rendered the same way PyPI does.

   .. code:: bash

      rm -rf dist/
      uv build
      uvx twine check --strict dist/*

   If new non-Python files were added to the package, make sure that
   ``MANIFEST.in`` covers them, and that they are in the wheel:

   .. code:: bash

      python -m zipfile -l dist/arouteserver-*.whl

7. Build and verify the docs:

   .. code:: bash

      uv sync --group docs
      cd docs ; uv run make html ; python3 -m http.server -b 127.0.0.1 8000 ; cd ..

8. Smoke-test the wheel in a clean virtualenv:

   .. code:: bash

      V=/tmp/ars-release-test ; rm -rf $V
      uv venv $V
      uv pip install -p $V dist/arouteserver-*.whl
      source $V/bin/activate

      arouteserver setup --dest-dir $V/cfg
      arouteserver configure --cfg $V/cfg/arouteserver.yml \
        --preset-answer daemon=bird version=2.19.2 asn=64496 router_id=192.0.2.1 \
          black_list=192.0.2.0/24,2001:db8::/32
      arouteserver check-config --cfg $V/cfg/arouteserver.yml
      arouteserver bird --cfg $V/cfg/arouteserver.yml -o /dev/null

      deactivate

   To test an upgrade, install the previous release from PyPI first
   (``uv pip install -p $V arouteserver==<previous>``), run ``setup`` and
   ``configure`` with it, then install the new wheel on top of it and run
   ``arouteserver verify-templates --cfg $V/cfg/arouteserver.yml``.

Publishing
----------

The version is read from the package:

.. code:: bash

   VERSION="$(python -c 'from pierky.arouteserver.version import __version__; print(__version__)')"

Dev releases, in the ``dev`` branch:

.. code:: bash

   git commit -a -m "v${VERSION}"
   git tag "v${VERSION}"
   git push origin dev --tags

Production releases, in the ``master`` branch:

.. code:: bash

   git commit -a -m "v${VERSION}"
   git tag "v${VERSION}"
   git push origin master --tags

Pushing a ``v*`` tag starts the release jobs of ``.github/workflows/cicd.yml``,
once the tests pass:

- every release is published to Test PyPI;
- releases whose tag doesn't contain ``alpha`` are published to PyPI too;
- the Docker images are pushed to Docker Hub (``<version>`` and
  ``<version>-pypy3``); for stable releases (``X.YY.Z``) ``latest`` and
  ``latest-pypy3`` are updated too.

Finally, create the new release on GitHub.
