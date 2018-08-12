import os
from os.path import abspath, dirname, join
from setuptools import setup, find_packages

"""
New release procedure

- ./utils/update_fingerprints.py

- ./utils/update_tests

- edit pierky/arouteserver/version.py

- edit CHANGES.rst

- verify RST syntax is ok
    python setup.py --long-description | rst2html.py --strict

- build and verify docs
    cd docs ; make html ; python -m SimpleHTTPServer 8000 ; cd ..

- new files to be added to MANIFEST.in?

- python setup.py sdist

- ~$ ./arouteserver/utils/test_new_rel

dev releases (in 'dev' branch):

    - git tag vX.YY.0-alpha1 (2, 3, ...)

    - git push origin dev --tags

prod releases (in 'master' branch):

    - git tag vX.YY.0

    - git push origin master --tags

# upload to PyPi done by CD tools in GitHub/Travis
#- ~/.local/bin/twine upload dist/*
#- git push

- edit new release on GitHub
"""

__version__ = None

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# Get proper long description for package
current_dir = dirname(abspath(__file__))
description = open(join(current_dir, "README.rst")).read()
changes = open(join(current_dir, "CHANGES.rst")).read()
long_description = '\n\n'.join([description, changes])
exec(open(join(current_dir, "pierky/arouteserver/version.py")).read())

install_requires = []
with open("requirements.txt", "r") as f:
    for line in f.read().split("\n"):
        if line:
            install_requires.append(line)

# Get the long description from README.md
setup(
    name="arouteserver",
    version=__version__,

    packages=["pierky", "pierky.arouteserver"],
    namespace_packages=["pierky"],
    package_data={
        "pierky.arouteserver": ["pierky/arouteserver/config.d/*",
                                "pierky/arouteserver/templates/*",
                                "pierky/arouteserver/tests/live_tests/skeleton/*.yml",
                                "pierky/arouteserver/tests/live_tests/skeleton/*.j2"]
    },
    include_package_data=True,
    
    license="GPLv3",
    description="A Python tool to automatically build (and test) configurations for BGP route servers.",
    long_description=long_description,
    url="https://github.com/pierky/arouteserver",
    download_url="https://github.com/pierky/arouteserver",

    author="Pier Carlo Chiodi",
    author_email="pierky@pierky.com",
    maintainer="Pier Carlo Chiodi",
    maintainer_email="pierky@pierky.com",

    install_requires=install_requires,
    tests_require=[
        "nose",
        "mock",
    ],
    test_suite="nose.collector",

    scripts=["scripts/arouteserver"],

    keywords=['BGP', 'Route server', 'BIRD', 'IP Routing'],

    classifiers=[
        "Development Status :: 4 - Beta",

        "Environment :: Console",

        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",

        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",

        "Operating System :: POSIX",
        "Operating System :: Unix",

        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",

        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Networking",
    ],
)
