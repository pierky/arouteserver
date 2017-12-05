#!/usr/bin/env python

import fileinput
import re
import sys

pat = re.compile("^(?:\*>\s+|\*\s+)?"
                 "([a-f0-9\.\:]+\/[0-9]{1,3})\s+"
                 "([a-f0-9\.\:]+)\s+"
                 "[0-9]+\s+"
                 "[0-9]+\s+"
                 "([0-9\s\{\}]+)\s+"
                 "[i|e|\?]"
                 "$")

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

err = False

for line_raw in fileinput.input():
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
