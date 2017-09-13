#!/usr/bin/env python

import os
from os.path import abspath, dirname, join
from setuptools import setup, find_packages
import sys

print("Calculating templates fingerprints...")
import yaml
from pierky.arouteserver.config.program import ConfigParserProgram
fps = ConfigParserProgram.calculate_fingerprints("templates")
fps_path = os.path.join("templates", ConfigParserProgram.FINGERPRINTS_FILENAME)
with open(fps_path, "w") as f:
    yaml.safe_dump(fps, f, default_flow_style=False)
