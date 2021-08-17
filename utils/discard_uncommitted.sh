#!/bin/bash

if [ "$1" == "tests" ]; then
    F="tests/live_tests/scenarios/*/routes/* tests/live_tests/scenarios/*/configs/ docs/_static/tests_*.html tests/real/general.html"
elif [ "$1" == "examples" ]; then
    F="examples/*/*.html examples/*/*.conf examples/*/template-context* docs/_static/examples_*.html"
else
    echo "Argument needed: tests | examples"
    exit 1
fi

echo "The following files will be 'git checkout --'ed: "
echo ""

FILES="$(git status --untracked-files=no -s -- $F | awk '{print $2}')"
git status --untracked-files=no -s -- $F

echo ""
echo -n "The files above will be 'git checkout --'ed: confirm? [yes/NO] "
read
if [ "${REPLY}" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

git checkout --force -- $FILES

echo "Done!"
