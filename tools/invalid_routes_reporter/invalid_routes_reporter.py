#!/usr/bin/env python

# Copyright (C) 2017 Pier Carlo Chiodi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
from email.mime.text import MIMEText
import json
import logging
from logging.config import fileConfig, dictConfig
from Queue import Queue, Empty, Full
import re
import smtplib
import sys
import threading
import time

DEFAULT_REJECT_REASON_RE_PATTERN = "^65520:(\d+)$"

class UpdatesProcessingThread(threading.Thread):

    def __init__(self, updates_q, alerts_queues,
                 reject_reason_pattern, networks_cfg):
        threading.Thread.__init__(self)

        self.updates_q = updates_q
        self.alerts_queues = alerts_queues

        self.reject_reason_pattern = re.compile(reject_reason_pattern)
        self.networks_cfg = networks_cfg

        self.quit_flag = False

    def get_reject_reason(self, std_comms, lrg_comms, ext_comms):
        for fmt in (std_comms, lrg_comms, ext_comms):
            if not fmt or len(fmt) == 0:
                continue

            reject_cause_zero_found = False
            reject_reason = None

            for comm in fmt:
                match = self.reject_reason_pattern.match(comm)

                if not match:
                    continue

                reason = int(match.group(1))
                if reason == 0:
                    reject_cause_zero_found = True
                else:
                    reject_reason = reason

                if reject_cause_zero_found and reject_reason:
                    return reject_reason

    def get_recipient_ids(self, as_path, next_hop):
        ids = []

        if as_path:
            ids.append("AS{}".format(as_path[0]))

        if next_hop:
            for asn in self.networks_cfg:
                if "neighbors" in self.networks_cfg[asn]:
                    neighbors = self.networks_cfg[asn]["neighbors"]
                    if next_hop in [n.lower() for n in neighbors]:
                        ids.append(asn)

        return ids

    def process_route(self, prefix, next_hop, as_path, std_comms, lrg_comms, ext_comms):
        reject_reason = self.get_reject_reason(std_comms, lrg_comms, ext_comms)

        if not reject_reason:
            return

        recipient_ids = self.get_recipient_ids(as_path, next_hop)

        route = {
            "ts": int(time.time()),
            "prefix": prefix,
            "next_hop": next_hop,
            "as_path": as_path,
            "std_comms": std_comms,
            "lrg_comms": lrg_comms,
            "ext_comms": ext_comms,
            "reject_reason_code": reject_reason,
            "recipient_ids": recipient_ids
        }
        logging.debug("Enqueuing route: {}".format(str(route)))
        for alerts_q in self.alerts_queues:
            alerts_q.put(route)

    @staticmethod
    def comms_to_str(lst):
        if not lst or len(lst) == 0:
            return []
        return [":".join(map(str, parts)) for parts in lst]

    def run(self):
        while True:
            try:
                obj = self.updates_q.get(block=True, timeout=0.5)
                update = obj["neighbor"]["message"]["update"]

                as_path = None
                std_comms = None
                lrg_comms = None
                ext_comms = None
                next_hop = None
                if "attribute" in update:
                    attribute = update["attribute"]
                    as_path = attribute.get("as-path")
                    std_comms = attribute.get("community")
                    lrg_comms = attribute.get("large-community")
                    ext_comms = attribute.get("extended-community")

                if "announce" in update:
                    announce = update["announce"]
                    for afi_safi in announce:
                        if afi_safi not in ("ipv4 unicast", "ipv6 unicast"):
                            continue
                        for next_hop in announce[afi_safi]:
                            for prefix in announce[afi_safi][next_hop]:
                                self.process_route(prefix, next_hop, as_path,
                                                   self.comms_to_str(std_comms),
                                                   self.comms_to_str(lrg_comms),
                                                   self.comms_to_str(ext_comms))

                self.updates_q.task_done()
            except Empty:
                if self.quit_flag:
                    logging.debug("Quitting collector")
                    return

class NotifierThread(threading.Thread):

    REJECT_REASONS = {
        "1": "Invalid AS_PATH length",
        "2": "Prefix is bogon",
        "3": "Prefix is in global blacklist",
        "4": "Invalid AFI",
        "5": "Invalid NEXT_HOP",
        "6": "Invalid left-most ASN",
        "7": "Invalid ASN in AS_PATH",
        "8": "Transit-free ASN in AS_PATH",
        "9": "Origin ASN not in IRRDB AS-SETs",
        "10": "IPv6 prefix not in global unicast space",
        "11": "Prefix is in client blacklist",
        "12": "Prefix not in IRRDB AS-SETs",
        "13": "Invalid prefix length",
        "14": "RPKI INVALID route",
    }

    def __init__(self, alerts_q, alerter_cfg):
        threading.Thread.__init__(self)

        self.alerts_q = alerts_q
        self.quit_flag = False

        self.cfg = alerter_cfg

        self.data = {}
        for recipient_id in self.cfg["recipients"]:
            recipient = self.cfg["recipients"][recipient_id]

            self.data[str(recipient_id)] = {
                "id": recipient_id,
                "config": {
                    "info": recipient["info"] if "info" in recipient else None,
                    "max_routes": int(
                        recipient.get("max_routes",
                                      self.cfg.get("max_routes", 30))
                    ),
                    "max_wait": int(
                        recipient.get("max_wait",
                                      self.cfg.get("max_wait", 900))
                    ),
                    "min_wait": int(
                        recipient.get("min_wait",
                                      self.cfg.get("min_wait", 300))
                    )
                },
                "last_flush": None,
                "routes": []
            }

        self.validate_config()

    def validate_config(self):
        pass

    def process_alert(self, route):
        recipients = list(set(route["recipient_ids"]))

        logging.debug("Processing alert for {}, recipients {}".format(
            str(route), str(recipients)
        ))

        if "*" in self.data:
            recipients.append("*")

        for recipient_id in recipients:
            if not recipient_id in self.data:
                continue

            recipient = self.data[recipient_id]

            if len(recipient["routes"]) < recipient["config"]["max_routes"]:
                recipient["routes"].append(route)

    def _flush_recipient(self, recipient):
        raise NotImplementedError()

    def flush_recipient(self, recipient):
        ts = int(time.time())

        self._flush_recipient(recipient)

        recipient["last_flush"] = ts
        recipient["routes"] = []

    def flush(self):
        ts = int(time.time())
        logging.debug("Flush {}".format(ts))
        for recipient_id in self.data:
            recipient = self.data[recipient_id]

            routes_cnt = len(recipient["routes"])

            if routes_cnt == 0:
                continue

            if recipient["config"]["min_wait"] and recipient["last_flush"]:
                if recipient["last_flush"] + recipient["config"]["min_wait"] > ts:
                    logging.debug("Skipping {} for min_wait".format(recipient_id))
                    continue

            if routes_cnt >= recipient["config"]["max_routes"]:
                self.flush_recipient(recipient)
                continue

            if recipient["config"]["max_wait"]:
                if not recipient["last_flush"] or \
                    recipient["last_flush"] + recipient["config"]["max_wait"] < ts:

                    self.flush_recipient(recipient)
                    continue

    def get_reject_reason_descr(self, reason_code):
        if str(reason_code) in self.REJECT_REASONS:
            return self.REJECT_REASONS[str(reason_code)]
        else:
            return "Unknown reason code {}".format(reason_code)

    def run(self):
        while True:
            try:
                alert = self.alerts_q.get(block=True, timeout=1)
                self.process_alert(alert)
                self.alerts_q.task_done()
            except Empty:
                if self.quit_flag:
                    logging.debug("Quitting notifier")
                    return
            self.flush()

class EMailNotifierThread(NotifierThread):

    def __init__(self, *args, **kwargs):
        super(EMailNotifierThread, self).__init__(*args, **kwargs)

        self.smtp_connection = None

    def validate_config(self):
        try:
            if not "host" in self.cfg:
                raise ValueError("missing 'host' parameter")
            self.host = self.cfg["host"]

            if not "from_addr" in self.cfg:
                raise ValueError("missing 'from_addr' parameter")
            self.from_addr = self.cfg["from_addr"]

            if not "template_file" in self.cfg:
                raise ValueError("missing 'template_file' parameter")
            self.template_file = self.cfg["template_file"]

            self.port = int(self.cfg.get("port", 25))
            self.username = self.cfg.get("username", None)
            self.password = self.cfg.get("password", None)
            self.subject = self.cfg.get("subject", "Bad routes received!")

            with open(self.template_file, "r") as f:
                self.template = f.read()
        except ValueError as e:
            raise ValueError(
                "Error in the configuration of the alerter: {}".format(
                    str(e)
                )
            )

        for recipient_id in self.data:
            recipient = self.data[recipient_id]
            try:
                if "email" not in recipient["config"]["info"]:
                    raise ValueError("missing 'email'.")
            except ValueError as e:
                raise ValueError(
                    "Error in the configuration of recipient '{}': "
                    "'{}'".format(
                        recipient_id, str(e)
                    )
                )

    def _format_list_of_routes(self, routes):
        res = ""
        for route in routes:
            if res:
                res += "\n"
            res += "prefix:      {}\n".format(route["prefix"])
            res += " - AS_PATH:  {}\n".format(" ".join(map(str, route["as_path"])))
            res += " - NEXT_HOP: {}\n".format(route["next_hop"])
            res += " - reject reason: {}\n".format(
                self.get_reject_reason_descr(route["reject_reason_code"])
            )
        return res

    def _connect_smtp(self, force=False):
        if self.smtp_connection is not None and not force:
            return True

        try:
            logging.debug("Connecting to SMTP server {}:{}".format(
                self.host, self.port))
            smtp = smtplib.SMTP(self.host, self.port)
            if self.username and self.password:
                smtp.login(self.username, self.password)
            self.smtp_connection = smtp
        except Exception as e:
            logging.error("Error while connecting to SMTP server: "
                          "{}".format(str(e)),
                          exc_info=True)
            return False

        return True

    def _send_email(self, from_addr, to_addrs, msg):
        if self._connect_smtp():
            try:
                try:
                    self.smtp_connection.sendmail(from_addr, to_addrs, msg)
                    return
                except smtplib.SMTPServerDisconnected as e:
                    logging.debug("SMTP disconnected: {} - reconnecting".format(str(e)))

                    if self._connect_smtp(force=True):
                        self.smtp_connection.sendmail(from_addr, to_addrs, msg)
                        return
            except Exception as e:
                logging.error("Error while sending email to {}: "
                              "{}".format(email_addresses, str(e)),
                              exc_info=True)

    def _flush_recipient(self, recipient):
        email_addresses = list(set(recipient["config"]["info"]["email"]))

        logging.info("Sending email to {} ({}) for {}".format(
            recipient["id"],
            ", ".join(email_addresses),
            ", ".join([route["prefix"] for route in recipient["routes"]])
        ))

        data = {
            "id": recipient["id"],
            "from_addr": self.from_addr,
            "subject": self.subject,
            "routes_list": self._format_list_of_routes(recipient["routes"])
        }
        msg = MIMEText(self.template.format(**data))
        msg['Subject'] = self.subject
        msg['From'] = self.from_addr
        msg['To'] = ", ".join(email_addresses)

        self._send_email(self.from_addr, email_addresses, msg.as_string())

class LoggerThread(NotifierThread):

    def __init__(self, *args, **kwargs):
        super(LoggerThread, self).__init__(*args, **kwargs)

        self.file = None

    def validate_config(self):
        try:
            if not "path" in self.cfg:
                raise ValueError("missing 'path' parameter")
            self.path = self.cfg["path"]

            if "append" in self.cfg:
                self.append = bool(self.cfg["append"])
            else:
                self.append = False

            if "template" in self.cfg:
                self.template = self.cfg["format"]
            else:
                self.template = ("{id},{ts},{prefix},{as_path},{next_hop},"
                                 "{reject_reason_code},{reject_reason}")

            if len(self.cfg["recipients"]) > 1 and \
                "*" in self.cfg["recipients"]:

                raise ValueError(
                    "when the wildcard recipient '*' is used, no other "
                    "recipients can be used"
                )

        except ValueError as e:
            raise ValueError(
                "Error in the configuration of the alerter: {}".format(
                    str(e)
                )
            )

    def _open_file(self):
        if self.file is not None:
            return True

        try:
            self.file = open(self.path, "a" if self.append else "w")
        except Exception as e:
            logging.error(
                "Error while opening the destination file '{}': {} - "
                "Quitting the logger thread.".format(
                    self.path, str(e)
                )
            )
            self.quit_flag = True
            return

        return True

    def _flush_recipient(self, recipient):
        if self._open_file():
            for route in recipient["routes"]:
                reject_reason_code = route["reject_reason_code"]
                reject_reason = self.get_reject_reason_descr(reject_reason_code)
                data = route.copy()
                data.update({
                    "id": recipient["id"],
                    "reject_reason": reject_reason
                })
                self.file.write(self.template.format(**data) + "\n")
                self.file.flush()

def read_alerter_config(path):
    try:
        with open(path, "r") as f:
           cfg = json.load(f)
    except Exception as e:
        logging.error(
            "Can't read alerter configuration from '{}': {}".format(
                path, str(e)
            ), exc_info=True)
        return

    err = "Error in the configuration of alerter '{}': ".format(path)
    if not "type" in cfg:
        logging.error(err + "missing 'type' option.")
        return

    if cfg["type"] not in ["email", "log"]:
        logging.error(err + "type '{}' is unknown".format(
            cfg["type"]
        ))
        return

    return cfg

def read_networks_config(path):
    try:
        with open(path, "r") as f:
            cfg = json.load(f)
    except Exception as e:
        logging.error(
            "Can't read networks configuration from '{}': {}".format(
                path, str(e)
            ), exc_info=True)
        return

    err = "Error in the networks configuration file '{}': ".format(path)
    for k in cfg:
        if not re.match("^AS\d+$", k):
            logging.error("invalid key: '{}'; "
                          "keys must be in the 'AS<n>' format.".format(k))
            return

        if "neighbors" in cfg[k]:
            if not isinstance(cfg[k]["neighbors"], list):
                cfg[k]["neighbors"] = [cfg[k]["neighbors"]]

    return cfg

def check_re_pattern(args):
    if args.re_pattern[0] != "^":
        raise ValueError(
            "the first character must be a caret (^) "
            "in order to match the start of the "
            "textual representation of any BGP community"
        )
    if args.re_pattern[-1] != "$":
        raise ValueError(
            "the last character must be a dollar ($) "
            "in order to match the end of the "
            "textual representation of any BGP community"
        )
    try:
        re_pattern = re.compile(args.re_pattern)
    except Exception as e:
        raise ValueError(
            "can't compile the regex pattern: {}".format(str(e))
        )
    if re_pattern.groups != 1:
        raise ValueError(
            "the pattern must contain 1 group to match "
            "the reject reason numerical identifier on "
            "the last part of any BGP community"
        )

def run(args):
    try:
        check_re_pattern(args)
    except ValueError as e:
        logging.error("Invalid reject reason pattern: {}".format(str(e)))
        return False

    networks_cfg = read_networks_config(args.networks_config_file)

    updates_q = Queue()
    alerts_queues = []

    notifier_threads = []

    for alerter_config_file_path in args.alerter_config_file:
        alerter_cfg = read_alerter_config(alerter_config_file_path)
        if not alerter_cfg:
            return False

        alerts_q = Queue()
        alerts_queues.append(alerts_q)

        if alerter_cfg["type"] == "email":
            notifier_class = EMailNotifierThread
        elif alerter_cfg["type"] == "log":
            notifier_class = LoggerThread
        else:
            raise NotImplementedError("Notifier class unknown")

        try:
            notifier = notifier_class(alerts_q, alerter_cfg)
        except Exception as e:
            logging.error(
                "Error while creating the notifier from '{}': {}".format(
                    alerter_config_file_path, str(e)
                ), exc_info=not isinstance(e, (ValueError, IOError))
            )
            return False

        notifier_threads.append(notifier)

    for notifier in notifier_threads:
        notifier.start()

    collector = UpdatesProcessingThread(updates_q, alerts_queues,
                                        args.re_pattern, networks_cfg)
    collector.start()

    empty_lines_counter = 0
    first_eor_received = False
    errors_counter = 0

    sys.stdout.write(
        "Waiting for UPDATE messages in ExaBGP JSON format on stdin...\n"
    )

    while True:
        try:
            line = sys.stdin.readline().strip()

            if not line:
                empty_lines_counter += 1
                if empty_lines_counter > 100:
                    break
                continue
            empty_lines_counter = 0

            try:
                obj = json.loads(line)
            except Exception as e:
                logging.error("Error while parsing JSON message: "
                              "{}".format(str(e)))
                errors_counter += 1
                if errors_counter >= args.max_error_cnt:
                    break
                continue

            if not "exabgp" in obj:
                logging.error("Unexpected JSON format: 'exabgp' key not found")
                errors_counter += 1
                if errors_counter >= args.max_error_cnt:
                    break
                continue

            if obj["type"] != "update":
                continue

            if "neighbor" not in obj:
                logging.error("Unexpected JSON format: 'neighbor' key not found")
                errors_counter += 1
                if errors_counter >= args.max_error_cnt:
                    break
                continue
            neighbor = obj["neighbor"]

            ip_ver = 6 if ":" in neighbor["ip"] else 4

            if "message" not in neighbor:
                logging.error("Unexpected JSON format: 'message' key not found")
                errors_counter += 1
                if errors_counter >= args.max_error_cnt:
                    break
                continue
            message = neighbor["message"]

            if "update" not in message:
                logging.error("Unexpected JSON format: 'update' key not found")
                errors_counter += 1
                if errors_counter >= args.max_error_cnt:
                    break
                continue
            update = message["update"]

            if "announce" not in update:
                logging.error("Unexpected JSON format: 'announce' key not found")
                errors_counter += 1
                if errors_counter >= args.max_error_cnt:
                    break
                continue
            announce = update["announce"]

            if "ipv{} unicast".format(ip_ver) not in announce:
                logging.error("Unexpected JSON format: 'ipv{} unicast' "
                              "key not found".format(ip_ver))
                errors_counter += 1
                if errors_counter >= args.max_error_cnt:
                    break

                continue

            if "null" in announce["ipv{} unicast".format(ip_ver)] and \
                "eor" in announce["ipv{} unicast".format(ip_ver)]["null"]:

                logging.debug("Received EOR")
                if not first_eor_received:
                    logging.info("Received first EOR")
                first_eor_received = True
                continue

            if first_eor_received or not args.wait_for_first_eor:
                updates_q.put(obj)

        except KeyboardInterrupt as e:
            break
        except IOError as e:
            break
        except Exception as e:
            logging.error("Unhandled exception: {}".format(str(e)),
                          exc_info=True)
            break

    if errors_counter >= args.max_error_cnt:
        logging.error("Aborting: max number of errors reached "
                      "({})".format(args.max_error_cnt))

    logging.debug("Ending - waiting for collector thread...")
    collector.quit_flag = True
    for notifier in notifier_threads:
        notifier.quit_flag = True

    collector.join()
    logging.debug("Collector closed")

    logging.debug("Waiting for notifier threads...")
    for notifier in notifier_threads:
        notifier.join()
    logging.debug("Notifiers closed")

    return True

def main():
    parser = argparse.ArgumentParser(
       description="Invalid routes notifier. "
                   "To be used as an ExaBGP process to elaborate "
                   "UPDATE messages in JSON encoded parsed format.",
       epilog="Copyright (c) {} - Pier Carlo Chiodi - "
              "https://pierky.com".format(2017)
    )

    parser.add_argument(
        "networks_config_file",
        help="The file containing the list of ASNs and their peers "
             "IP addresses."
    )
    parser.add_argument(
        "alerter_config_file",
        nargs="+",
        help="One or more alerter configuration file(s)."
    )

    default = DEFAULT_REJECT_REASON_RE_PATTERN
    parser.add_argument(
        "-r", "--reject-reason-pattern",
        help="Regular expression pattern used to extract the "
             "reject reason from the (standard|large|extended) "
             "BGP communities. "
             "Default: {}".format(default),
        default=default,
        dest="re_pattern"
    )

    default = 100
    parser.add_argument(
        "--max-error-cnt",
        type=int,
        help="While processing routes from ExaBGP, quit if the "
             "number of errors exceed this value. "
             "Default: {}.".format(default),
        default=default,
        dest="max_error_cnt"
    )

    default = False
    parser.add_argument(
        "-w", "--wait-for-first-eor",
        action="store_true",
        help="Start processing routes only after the first EOR "
             "is received. "
             "Default: {}.".format(default),
        default=default,
        dest="wait_for_first_eor"
    )

    parser.add_argument(
        "--logging-config-file",
        help="Logging configuration file, in Python fileConfig() format ("
            "https://docs.python.org/2/library/logging.config.html"
            "#configuration-file-format)",
        dest="logging_config_file")

    parser.add_argument(
        "--logging-level",
        help="Logging level. Overrides any configuration given in the "
             "logging configuration file.",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        dest="logging_level"
    )

    args = parser.parse_args()

    if args.logging_config_file:
        try:
            fileConfig(args.logging_config_file)
        except Exception as e:
            logging.error(
                "Error processing the logging configuration file "
                "{}: {}".format(args.logging_config_file, str(e))
            )
        return

    if args.logging_level:
        dictConfig({
            "version": 1,
            "root": {
                "level": args.logging_level
            },
            "incremental": True
        })

    if run(args):
        sys.exit(0)
    else:
        sys.exit(1)

main()
