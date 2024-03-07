#!/usr/bin/env python3
"""Tool that can check the syntax of the ADRs in the standards directory

See scs-0001-v1-sovereign-cloud-standards.md for reference.
"""

import collections
import datetime
import os
import os.path
import sys

import yaml


# quoting scs-0001-v1-sovereign-cloud-standards.md regarding front-matter fields:

# | `type`          | REQUIRED                                                                   | one of `Procedural`, `Standard`, or `Decision Record`                                 |
# | `status`        | REQUIRED                                                                   | one of `Proposal`, `Draft`, `Stable`, `Deprecated`, or `Rejected`                     |
# | `track`         | REQUIRED                                                                   | one of `Global`, `IaaS`, `KaaS`, `IAM`, `Ops`                                         |
# | `obsoleted_at`  | REQUIRED if `status` is `Deprecated`                                       | ISO formatted date indicating the date after which the deprecation is in effect       |
# | `stabilized_at` | REQUIRED if `status` was ever `Stable`                                     | ISO formatted date indicating the date after which the document was considered stable |
# | `rejected_at`   | REQUIRED if `status` is `Rejected`                                         | ISO formatted date indicating the date on which the document was rejected             |
# | `replaced_by`   | RECOMMENDED if `status` is `Deprecated` or `Rejected`, FORBIDDEN otherwise | List of documents which replace this document.                                        |

UNDEFINED = object()


def optional(predicate):
    def check(value):
        return value is UNDEFINED or predicate(value)
    return check


def iso_date(value):
    try:
        return isinstance(value, datetime.date) or datetime.date.fromisoformat(value) and True
    except ValueError:
        return False


# map key to value-checker predicate
FRONT_MATTER_KEYS = {
    "type": ("Procedural", "Standard", "Decision Record").__contains__,
    "status": ("Proposal", "Draft", "Stable", "Deprecated", "Rejected").__contains__,
    "track": ("Global", "IaaS", "KaaS", "IAM", "Ops").__contains__,
    "obsoleted_at": optional(iso_date),
    "stabilized_at": optional(iso_date),
    "rejected_at": optional(iso_date),
}


def print_usage(file=sys.stderr):
    """Help output"""
    print("""Usage: chk_adrs.py PATH

This tool checks the syntax of the ADRs in PATH according to scs-0001-v1-sovereign-cloud-standards.

Arguments:
 PATH   path to the folder containing the adr documents (md files)
""", end='', file=file)


class Checker:
    def __init__(self):
        self.errors = 0

    def emit(self, s):
        print(f"ERROR: {s}", file=sys.stderr)
        self.errors += 1

    def check_names(self, mds):
        """Check the list `mds` of md file names for name collisions"""
        # count the occurrences of the prefixes of length 12, e.g., scs-0001-v1-
        # no duplicates allowed, except for documents in Proposal state (scs-xxxx-...)
        counts = collections.Counter([fn[:12] for fn in mds if fn[4:8].lower() != 'xxxx'])
        duplicates = sorted([fn for fn in mds if counts[fn[:12]] > 1])
        if duplicates:
            self.emit(f"duplicates found: {', '.join(duplicates)}")

    def check_front_matter(self, fn, front):
        """Check the dict `front` of front matter; `fn` is for context in error messages"""
        if front is None:
            self.emit(f"in {fn}: is missing front matter altogether")
            return
        # check each field in isolation
        errors = [
            key
            for key, predicate in FRONT_MATTER_KEYS.items()
            if not predicate(front.get(key, UNDEFINED))
        ]
        if errors:
            self.emit(f"in {fn}: syntax errors with key(s) {', '.join(errors)}")
        # now do cross-field checks
        status = front.get("status")
        if "replaced_by" in front and status not in ("Deprecated", "Rejected"):
            self.emit(f"in {fn}: replaced_by is set, but status does not match")
        if status == "Deprecated" and "obsoleted_at" not in front:
            self.emit(f"in {fn}: status is Deprecated, but deprecated_at date is missing")
        if status in ("Stable", "Deprecated") and "stabilized_at" not in front:
            self.emit(f"in {fn}: status is Stable or Deprecated, but stabilized_at date is missing")
        if status == "Rejected" and "rejected_at" not in front:
            self.emit(f"in {fn}: status is Rejected, but rejected_at date is missing")


def main(argv):
    if len(argv) != 2:
        raise RuntimeError("must specify exactly one argument, PATH")
    path = argv[1]
    mds = sorted([
        fn
        for fn in os.listdir(path)
        if fn.startswith("scs-") and fn.endswith(".md")
    ])
    checker = Checker()
    checker.check_names(mds)
    # now load each file and check front matter
    for fn in mds:
        with open(os.path.join(path, fn), "rb") as flo:
            loader = yaml.SafeLoader(flo)
            try:
                front = loader.get_data()
            finally:
                loader.dispose()
            checker.check_front_matter(fn, front)
    return checker.errors


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"CRITICAL: {e!s}", file=sys.stderr)
        sys.exit(1)
