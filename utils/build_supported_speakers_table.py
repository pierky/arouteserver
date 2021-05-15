#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import OrderedDict

BGP_SPEAKER_HEADER_ROWS = [
    ["**BIRD**", "**BIRD v2**", "**OpenBGPD**", "**OpenBGPD**"],
    ["",         "",            "",             "**Portable**"]
]
BGP_SPEAKER_IDS = [
    "bird",      "bird2",       "openbgpd",     "openbgpd_portable"
]

features = OrderedDict()
notes = {
    "1": ("For max-prefix filtering, only the shutdown and "
          "the restart actions are supported by OpenBGPD. "
          "Restart is configured with a 15 minutes timer."),
    "2": ("OpenBGPD does not offer a way to delete extended "
          "communities using wildcard (rt xxx:\*): "
          "peer-ASN-specific extended communities (such as "
          "prepend_once_to_peer, do_not_announce_to_peer) "
          "are not scrubbed from routes that leave OpenBGPD "
          "route servers and so they are propagated to the "
          "route server clients."),
    "3": ("Multihop can be enabled only when path-hiding "
          "mitigation is turned off."),
}

output = ""

def add_feature(title, data=None):
    features[title] = data


def put_line(s=""):
    global output
    output += s + "\n"


def put_table_line(lengths, char="="):
    global output
    for length in lengths:
        output += char * length + " "
    output += "\n"


add_feature("Path hiding mitigation (RFC7947, 2.3.1)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})


add_feature("Basic filters:")
add_feature("NEXT_HOP enforcement - strict (RFC7948, 4.8)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("NEXT_HOP enforcement - same AS (RFC7948, 4.8)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Min and max IPv4/IPv6 prefix length", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Max AS_PATH length", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Reject invalid AS_PATHs (private/invalid ASNs)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Reject AS_PATHs containing transit-free ASNs", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Reject 'never via route-servers' ASNs", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Reject bogons", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Max-prefix limit", {
    "bird": True,
    "bird2": True,
    "openbgpd": {
        "value": True,
        "note": 1
    },
    "openbgpd_portable": {
        "value": True,
        "note": 1
    },
})


add_feature("Prefixes and origin ASNs validation:")
add_feature("IRR-based filters (RFC7948, 4.6.2)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("RPKI ROAs used as route objects", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Origin AS from ARIN Whois database dump", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("NIC.BR Whois data (slide n. 26) from Registro.br", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("RPKI-based filtering (BGP Prefix Origin Validation)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})


add_feature("Blackhole filtering support:")
add_feature("Optional NEXT_HOP rewriting", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Signalling via BLACKHOLE and custom communities)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Client-by-client control over propagation", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})


add_feature("Graceful shutdown support:")
add_feature("GRACEFUL_SHUTDOWN BGP Community", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Graceful shutdown of the route server itself", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})


add_feature("Control and informative communities:")
add_feature("Prefix/origin ASN in IRRDBs data", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Do (not) announce to any / peer / on RTT basis", {
    "bird": True,
    "bird2": True,
    "openbgpd": {
        "value": True,
        "note": 2
    },
    "openbgpd_portable": {
        "value": True,
        "note": 2
    },
})
add_feature("Prepend to any / peer / on RTT basis", {
    "bird": True,
    "bird2": True,
    "openbgpd": {
        "value": True,
        "note": 2
    },
    "openbgpd_portable": {
        "value": True,
        "note": 2
    },
})
add_feature("Add NO_EXPORT / NO_ADVERTISE to any / peer", {
    "bird": True,
    "bird2": True,
    "openbgpd": {
        "value": True,
        "note": 2
    },
    "openbgpd_portable": {
        "value": True,
        "note": 2
    },
})
add_feature("Custom informational BGP communities", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})


add_feature("Optional session features on a client-by-client basis:")
add_feature("Prepend route server ASN (RFC7947, 2.2.2.1)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Active sessions", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("GTSM (Generalized TTL Security Mechanism)", {
    "bird": True,
    "bird2": True,
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("Multihop sessions", {
    "bird": {
        "value": True,
        "note": 3
    },
    "bird2": {
        "value": True,
        "note": 3
    },
    "openbgpd": True,
    "openbgpd_portable": True,
})
add_feature("ADD_PATH capability (RFC7911)", {
    "bird": True,
    "bird2": True,
    "openbgpd": None,
    "openbgpd_portable": None,
})



rows = [
    ["**Feature**"] + BGP_SPEAKER_HEADER_ROWS[0],
    [""] + BGP_SPEAKER_HEADER_ROWS[1]
]
for title, data in features.items():
    if not data:
        rows.append(["**" + title + "**"])
        continue

    cols = [title]
    for speaker in BGP_SPEAKER_IDS:
        if isinstance(data[speaker], dict):
            value = data[speaker]["value"]
            note = data[speaker]["note"]
            if str(note) not in notes:
                raise ValueError(
                    "Error processing the feature {}: "
                    "note n. {} not reported in 'notes'.".format(
                        title, note
                    )
                )
        else:
            value = data[speaker]
            note = None

        if value is True:
            text = "Yes"
        elif value is False:
            text = "No"
        else:
            text = "N/A"

        if note:
            text += " :sup:`" + str(note) + "`"
        cols.append(text)

    rows.append(cols)

max_lenghts = [0, 0, 0, 0, 0]
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
        put_line("-" * (sum(max_lenghts) + len(max_lenghts) - 1))
    else:
        if row_idx >= 1:
            put_table_line(max_lenghts, char="-")

put_table_line(max_lenghts)
put_line()
put_line()

for note_n, note_text in notes.items():
    line = ":sup:`" + str(note_n) + "`: " + note_text
    put_line(line)
    put_line()


print(".. DO NOT EDIT: this file is automatically created by ../utils/build_supported_speakers_table.py")
print("")
print(output)
