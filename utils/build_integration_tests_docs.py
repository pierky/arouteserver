#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDPortablePreviousInstance

# Ignoring tests of previous portable release because it's only used in
# 'global', not really relevant to build the content of this doc file.
IGNORE_BGP_SPEAKERS = [
    "OpenBGPD " + OpenBGPDPortablePreviousInstance.BGP_SPEAKER_VERSION
]

output = ""

def put_line(s=""):
    global output
    output += s + "\n"


def put_table_line(lengths, char="="):
    global output
    for length in lengths:
        output += char * length + " "
    output += "\n"


last_ci_output = open("tests/last", "r").read()

tests_to_skip = [
    "setting instances up...",
    "instances setup ...",
    "dumping rs config...",
    "dumping routes...",
    "stopping instances...",
    "sessions are up",
]

unique_scenarios = set()
unique_tests_per_scenario = {}
bgp_speakers_per_test = {}
unique_bgp_speakers = set()
stats_per_bgp_speaker = {}

for line in last_ci_output.split("\n"):
    if not line:
        continue
    if not line.startswith("Live test, "):
        continue
    if any([test_to_skip in line for test_to_skip in tests_to_skip]):
        continue

    # Live test, BIRD, global scenario, IPv4, tag: control communities, don't announce to any ... ok

    rest = line.replace("Live test, ", "")
    # BIRD, global scenario, IPv4, tag: control communities, don't announce to any ... ok

    fields = rest.split(",")
    # ["BIRD", "global scenario", "IPv4", ...

    bgp_speaker = fields[0].strip()
    del fields[0]

    if bgp_speaker in IGNORE_BGP_SPEAKERS:
        continue

    rest = ",".join(fields)
    # global scenario, IPv4, tag: control communities, don't announce to any ... ok

    fields = rest.split(":")
    # ["global scenario, IPv4, tag", "control communities...

    scenario = fields[0].strip()
    del fields[0]

    rest = ":".join(fields)
    # control communities, don't announce to any ... ok

    if " SKIPPED" in rest:
        test = rest.split(" SKIPPED")[0].strip()
        test_result = None
    elif " PASSED" in rest:
        test = rest.split(" PASSED")[0].strip()
        test_result = True
    elif " FAILED" in rest:
        test = rest.split(" FAILED")[0].strip()
        test_result = False
    else:
        test = test.strip()
        test_result = False

    if bgp_speaker not in stats_per_bgp_speaker:
        stats_per_bgp_speaker[bgp_speaker] = {
            "ok": 0,
            "failed": 0,
            "skip": 0,
            "total": 0
        }
    stats_per_bgp_speaker[bgp_speaker]["total"] += 1
    if test_result is True:
        stats_per_bgp_speaker[bgp_speaker]["ok"] += 1
    elif test_result is False:
        stats_per_bgp_speaker[bgp_speaker]["failed"] += 1
    else:
        stats_per_bgp_speaker[bgp_speaker]["skip"] += 1

    unique_scenarios.add(scenario)

    if scenario not in unique_tests_per_scenario:
        unique_tests_per_scenario[scenario] = set()
    unique_tests_per_scenario[scenario].add(test)

    if scenario not in bgp_speakers_per_test:
        bgp_speakers_per_test[scenario] = {}
    if test not in bgp_speakers_per_test[scenario]:
        bgp_speakers_per_test[scenario][test] = {}
    bgp_speakers_per_test[scenario][test][bgp_speaker] = test_result

    unique_bgp_speakers.add(bgp_speaker)

rows = [
    ["**BGP speaker**", "**Total**", "**Passed ✔**", "**Failed ✖**", "**Skipped**"]
]
for bgp_speaker in sorted(stats_per_bgp_speaker):
    rows.append([
        bgp_speaker,
        str(stats_per_bgp_speaker[bgp_speaker]["total"]),
        str(stats_per_bgp_speaker[bgp_speaker]["ok"]),
        str(stats_per_bgp_speaker[bgp_speaker]["failed"]),
        str(stats_per_bgp_speaker[bgp_speaker]["skip"]),
    ])

max_lenghts = [0, 0, 0, 0, 0, 0]
for row in rows:
    for idx, field in enumerate(row):
        if len(field) > max_lenghts[idx]:
            max_lenghts[idx] = len(field)

put_line(".. DO NOT EDIT: this file is automatically created by ../utils/build_integration_tests_docs.py")
put_line("")

put_line("Total test cases per BGP speaker")
put_line("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
put_line("")

put_table_line(max_lenghts)

for row_idx, row in enumerate(rows):
    line = ""

    for col_idx, field in enumerate(row):
        line += field + " " * (max_lenghts[col_idx] - len(field)) + " "

    put_line(line)

put_table_line(max_lenghts)
put_line()

put_line("Scenarios")
put_line("~~~~~~~~~")
put_line("")

for scenario in sorted(unique_scenarios):
    put_line(scenario)
    put_line("+" * len(scenario))
    put_line()

    rows = []
    headers = ["**Test**"]
    for bgp_speaker in sorted(unique_bgp_speakers):
        headers.append("**" + bgp_speaker + "**")
    rows.append(headers)

    for test in sorted(unique_tests_per_scenario[scenario]):
        row = [test]
        for bgp_speaker in sorted(unique_bgp_speakers):
            if scenario in bgp_speakers_per_test and \
               test in bgp_speakers_per_test[scenario] and \
               bgp_speaker in bgp_speakers_per_test[scenario][test]:
                test_result = bgp_speakers_per_test[scenario][test][bgp_speaker]
                if test_result is True:
                    text = "✔"
                elif test_result is False:
                    text = "✖"
                else:
                    text = "skip"
            else:
                text = ""

            row.append(text)

        rows.append(row)

    max_lenghts = [0, 0, 0, 0, 0, 0]
    for row in rows:
        for idx, field in enumerate(row):
            if len(field) > max_lenghts[idx]:
                max_lenghts[idx] = len(field)

    put_table_line(max_lenghts)

    for row_idx, row in enumerate(rows):
        line = ""

        for col_idx, field in enumerate(row):
            line += field + " " * (max_lenghts[col_idx] - len(field)) + " "

        put_line(line)

        if len(row) == 1:
            put_line("-" * (sum(max_lenghts) + len(max_lenghts) - 2))

    put_table_line(max_lenghts)
    put_line()

print(output)
