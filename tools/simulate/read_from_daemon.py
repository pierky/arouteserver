#!/usr/bin/env python

import fileinput
import re
import sys
try:
    import mock
except ImportError:
    import unittest.mock as mock

from pierky.arouteserver.tests.live_tests.bird import BIRDInstance

class FakeBIRDInstance(BIRDInstance):

    def __init__(self, raw):
        self.raw = raw

        self.routes = []
        self.protocols_status = {}

    def _birdcl(self, cmd):
        if cmd.strip() == "show route all":
            return self.raw
        elif cmd.strip() == "show route all filtered":
            return ""
        else:
            raise NotImplementedError("birdcl command '{}' not implemented".format(cmd))

    def run_cmd(self, *args, **kwargs):
        raise NotImplementedError()

    def restart(self):
        raise NotImplementedError()

    def reload_config(self):
        raise NotImplementedError()

    def _get_protocols_status(self, *args, **kwargs):
        self.protocols_status = mock.MagicMock()
        self.protocols_status.__getitem__.return_value = {"ip": ""}

    def get_bgp_session(self, *args, **kwargs):
        raise NotImplementedError()

    def get_protocol_name_by_ip(self, *args, **kwargs):
        raise NotImplementedError()

    def log_contains(self, *args, **kwargs):
        raise NotImplementedError()

    def log_contains_errors(self, *args, **kwargs):
        raise NotImplementedError()

USAGE="""
This script reads routes from the output of BIRD 'show route all'
and OpenBGPD 'show rib' commands and convert them in the internal
format used by the 'simulate' script to build the list of BGP
announcements used to simulate the scenario.

Usage:

   read_from_daemon.py (bird | openbgpd) < source_file > dest_file
"""

if len(sys.argv) <= 1:
    print("ERROR: the source format must be specified")
    print("")
    print(USAGE)
    sys.exit(1)

src_format = sys.argv[1]

if src_format not in ("bird", "openbgpd"):
    print("ERROR: invalid source format; must be 'bird' or 'openbgpd'")
    sys.exit(1)

records = {}

def add(prefix, next_hop, as_path):
    peer_as = as_path.split(" ")[0]
    if peer_as not in records:
        records[peer_as] = {}
    if next_hop not in records[peer_as]:
        records[peer_as][next_hop] = []
    records[peer_as][next_hop].append({
        "prefix": prefix,
        "next_hop": next_hop,
        "as_path": as_path
    })

def read_from_openbgpd():
    pat = re.compile("^(?:\*>\s+|\*\s+)?"
                    "([a-f0-9\.\:]+\/[0-9]{1,3})\s+"
                    "([a-f0-9\.\:]+)\s+"
                    "[0-9]+\s+"
                    "[0-9]+\s+"
                    "([0-9\s\{\}]+)\s+"
                    "[i|e|\?]"
                    "$")

    err = False

    for line_raw in sys.stdin.readlines():
        line = line_raw.strip()
        if not line:
            continue
        if line.startswith("flags"):
            continue
        if line.startswith("origin"):
            continue

        match = pat.match(line)
        if not match:
            sys.stderr.write("ERROR: can't parse this line '{}'\n".format(line))
            err = True
        else:
            add(match.group(1), match.group(2), match.group(3).replace("{", "").replace("}", ""))

    return err

def read_from_bird():
    bird = FakeBIRDInstance(sys.stdin.read())
    for route in bird.get_routes(None):
        add(route.prefix, route.next_hop.split(" ")[0], route.as_path)

if src_format == "bird":
    err = read_from_bird()
elif src_format == "openbgpd":
    err = read_from_openbgpd()
else:
    raise NotImplementedError()

for asn in records:
    for next_hop in records[asn]:
        for msg in records[asn][next_hop]:
            sys.stdout.write(
                "{a_w},{next_hop},{peer_as},{prefix},{as_path}\n".format(
                    a_w="A",
                    next_hop=msg["next_hop"],
                    peer_as=asn,
                    prefix=msg["prefix"],
                    as_path=msg["as_path"]
                )
            )

if err:
    sys.exit(1)

sys.exit(0)
