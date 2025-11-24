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
# | `deprecated_at` | REQUIRED if `status` is `Deprecated`                                       | ISO formatted date indicating the date after which the deprecation is in effect       |
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
    "deprecated_at": optional(iso_date),
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
        self.stable = collections.defaultdict(set)

    def emit(self, s):
        print(f"ERROR: {s}", file=sys.stderr)
        self.errors += 1

    def check_name(self, name):
        if not name.startswith('scs-'):
            return
        components = name.split('-')
        if len(components) < 4:
            self.emit(f"document name must have at least four components separated by '-': {name}")
            return
        doc_no = components[1]
        v_no = components[2][1:]
        if len(doc_no) != 4 or not (doc_no.isnumeric() or doc_no.lower() == 'xxxx'):
            self.emit(f"document code must have format NNNN, found {components[1]}")
        if components[2][:1] not in ("v", "w") or not (v_no.isnumeric() or v_no.upper() == 'N'):
            self.emit(f"document version must have format vN or wN, found: {components[2]}")

    def check_names(self, mds):
        """Check the list `mds` of md file names for name collisions"""
        # count the occurrences of the prefixes of length 12, e.g., scs-0001-v1-
        # no duplicates allowed, except for documents in Proposal state (scs-xxxx-...)
        counts = collections.Counter([fn[:12] for fn in mds if fn[4:8].lower() != 'xxxx'])
        duplicates = sorted([fn for fn in mds if counts[fn[:12]] > 1])
        if duplicates:
            self.emit(f"duplicates found: {', '.join(duplicates)}")
        for key, fns in self.stable.items():
            if len(fns) > 1:
                self.emit(f"duplicate stable: {fns}")

    def _check_front_matter_supplement(self, fn, front, filenames):
        typ = front.get('type')
        if typ != "Supplement":
            self.emit(f"in {fn}: type must be Supplement, is {typ}")
        if 'status' in front:
            self.emit(f"in {fn}: Supplement shouldn't have status field")
        supplements = front.get("supplements")
        if not isinstance(supplements, list):
            self.emit(f"in {fn}: field 'supplements' must be a list")
        # NOTE could check that each entry refers to a file that exists
        for fn2 in supplements:
            if fn2 not in filenames:
                self.emit("in {fn}: field 'supplements' refers to unknown {fn2}")

    def check_front_matter(self, fn, front, filenames):
        """Check the dict `front` of front matter

        The argument `fn` is mainly for context in error messages, but also to distinguish document types.
        """
        if front is None:
            self.emit(f"in {fn}: is missing front matter altogether")
            return
        if fn[9] == 'w':
            return self._check_front_matter_supplement(fn, front, filenames)
        if fn[9] != 'v':
            print(f"skipping non-primary {fn}", file=sys.stderr)
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
        if status == "Deprecated" and "deprecated_at" not in front:
            self.emit(f"in {fn}: status is Deprecated, but deprecated_at date is missing")
        if status in ("Stable", "Deprecated") and "stabilized_at" not in front:
            self.emit(f"in {fn}: status is Stable or Deprecated, but stabilized_at date is missing")
        if status == "Rejected" and "rejected_at" not in front:
            self.emit(f"in {fn}: status is Rejected, but rejected_at date is missing")
        if status == "Stable":
            self.stable[fn[4:8]].add(fn)


def _load_front_matter(path):
    with open(path, "rb") as flo:
        loader = yaml.SafeLoader(flo)
        try:
            return loader.get_data()
        finally:
            loader.dispose()


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
    for fn in mds:
        checker.check_name(fn)
        checker.check_front_matter(fn, _load_front_matter(os.path.join(path, fn)), mds)
    checker.check_names(mds)
    return checker.errors


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception as e:
        print(f"CRITICAL: {e!s}", file=sys.stderr)
        sys.exit(1)
