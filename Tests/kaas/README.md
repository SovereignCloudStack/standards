# Test suite for SCS-compatible KaaS

## Usage

See [README "KaaS Checks"](../README.md#kaas-checks)

## Development environment

This part is about improving the KaaS tests, not for running the conformance tests.

### requirements

* [docker](https://docs.docker.com/engine/install/)
* [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
* [sonobuoy](https://sonobuoy.io/docs/v0.57.1/#installation)

### setup for development

1. Generate python 3.10 env

   ```bash
   sudo apt-get install python3.10-dev
   virtualenv -p /usr/bin/python3.10 venv
   echo "*" >> venv/.gitignore
   source venv/bin/activate
   (venv) curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10
   (venv) python3.10 -m pip install --upgrade pip
   (venv) python3.10 -m pip --version
   ```

2. Install dependencies:

   ```bash
   (venv) pip install pip-tools
   (venv) pip-compile requirements.in
   (venv) pip-sync requirements.txt
   ```

3. Set environment variables and launch the process:

   ```bash
   (venv) export CLUSTER_PROVIDER="kind"
   (venv) python run.py
   ```
