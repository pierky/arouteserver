#!/usr/bin/env python

import os

import yaml

from pierky.arouteserver.config.program import ConfigParserProgram

print("Calculating templates fingerprints...")
fps = ConfigParserProgram.calculate_fingerprints("templates")
fps_path = os.path.join("templates", ConfigParserProgram.FINGERPRINTS_FILENAME)
with open(fps_path, "w") as f:
    yaml.safe_dump(fps, f, default_flow_style=False)
