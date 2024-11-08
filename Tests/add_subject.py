#!/usr/bin/env python3
# vim: set ts=4 sw=4 et:
#
# add_subject.py
#
# (c) Matthias Büchse <matthias.buechse@cloudandheat.com>
# SPDX-License-Identifier: Apache-2.0
import base64
import getpass
import os
import os.path
import re
import shutil
import subprocess
import sys

try:
    from passlib.context import CryptContext
    import argon2  # noqa:F401
except ImportError:
    print('Missing passlib and/or argon2. Please do:\npip install passlib argon2_cffi', file=sys.stderr)
    sys.exit(1)

# see ../compliance-monitor/monitor.py
CRYPTCTX = CryptContext(schemes=('argon2', 'bcrypt'), deprecated='auto')
SSH_KEYGEN = shutil.which('ssh-keygen')
SUBJECT_RE = re.compile(r"[a-zA-Z0-9_\-]+")


def main(argv, cwd):
    if len(argv) != 1:
        raise RuntimeError("Need to supply precisely one argument: name of subject")
    subject = argv[0]
    print(f"Attempt to add subject {subject!r}")
    keyfile_path = os.path.join(cwd, '.secret', 'keyfile')
    tokenfile_path = os.path.join(cwd, '.secret', 'tokenfile')
    if os.path.exists(keyfile_path):
        raise RuntimeError(f"Keyfile {keyfile_path} already present. Please proceed manually")
    if os.path.exists(tokenfile_path):
        raise RuntimeError(f"Tokenfile {tokenfile_path} already present. Please proceed manually")
    if not SUBJECT_RE.fullmatch(subject):
        raise RuntimeError(f"Subject name {subject!r} using disallowed characters")
    sanitized_subject = subject.replace('-', '_')
    print("Creating API key...")
    while True:
        password = getpass.getpass("Enter passphrase: ")
        if password == getpass.getpass("Repeat passphrase: "):
            break
        print("No match. Try again...")
    token = base64.b64encode(f"{subject}:{password}".encode('utf-8'))
    hash_ = CRYPTCTX.hash(password)
    with open(tokenfile_path, "wb") as fileobj:
        fileobj.write(token)
    print("Creating key file using `ssh-keygen`...")
    subprocess.check_call([SSH_KEYGEN, '-t', 'ed25519', '-C', sanitized_subject, '-f', keyfile_path, '-N', '', '-q'])
    with open(keyfile_path + '.pub', "r") as fileobj:
        pubkey_components = fileobj.readline().split()
    print(f'''
The following SECRET files have been created:

  - {keyfile_path}
  - {tokenfile_path}

They are required for submitting test reports. You MUST keep them secure and safe.

Insert the following snippet into compliance-monitor/bootstrap.yaml:

  - subject: {subject}
    api_keys:
      - "{hash_}"
    keys:
      - public_key: "{pubkey_components[1]}"
        public_key_type: "{pubkey_components[0]}"
        public_key_name: "primary"

Make sure to submit a pull request with the changed file. Otherwise, the reports cannot be submitted.
''', end='')


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:], cwd=os.path.dirname(sys.argv[0]) or os.getcwd()) or 0)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
