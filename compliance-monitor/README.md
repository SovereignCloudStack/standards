# SCS compliance monitor

A service with a REST-like interface, backed by Postgresql, to manage data about compliance of subjects
with SCS certificate requirements.

## Setup

The first two sections have been adapted from
<https://github.com/SovereignCloudStack/standards/blob/main/Tests/README.md>.

### Python dependencies

On your Linux machine, please ensure you have installed the dependencies
from `requirements.txt`. We recommended using Python >= 3.10 and to install the
requirements into a virtualenv as follows:

```shell
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Updating Python dependencies

We manage Python dependencies in two files: `requirements.in` and `requirements.txt`.
The former one is meant to be edited by humans, whereas the latter one is
generated by `pip-compile` and contains an exact listing of *all* dependencies,
including transitive ones.

`pip-compile` can be installed via `pip install pip-tools`.
It needs to be run in two cases:

1. You modified `requirements.in` (e.g., added a new dependency): run
   `pip-compile requirements.in`.
2. You want to bump the pinned dependencies: run `pip-compile --upgrade requirements.in`.

Note: The Python version used for running `pip-compile` should be consistent. The currently
used version is documented in the header of the `requirements.txt`.

### Postgresql

You need running Postgresql. For instance, run it in a container like so:

```shell
docker run --network=host --rm -v $(pwd)/data:/var/lib/postgresql/data -it --name postgres -e POSTGRES_PASSWORD=mysecretpassword postgres
```

### Monitor service

Run the service as follows:

```shell
./monitor.py --psqlpw mysecretpassword --port 8080 --bootstrap bootstrap.yaml
```

The service will automatically create or update the database schema as needed, and it will load any records
from the given bootstrap file into the database; this file should at least contain credentials for one user,
because otherwise you won't be able to post new data. See the dedicated section for details.

To use the service in production, it is strongly recommended to set up a reverse proxy with SSL.

## Bootstrap file

This file will be read and the database updated accordingly when the service is started, as well as upon the
corresponding signal.

```yaml
accounts:
  - subject: admin  # usually the subject under test, but this one is a special account
    api_key: "secret api key"  # needed for basic auth
    public_key: "..."  # needed to check signature of posted material
    roles:
      # anyone (even non-authenticated) can read public details for any subject
      # any account can read the non-public details of compliance results of their subject
      # any account can append results for their own subject
      # - append_any  # can append results for any subject
      - read_any  # can read non-public details of compliance results for any subject
      - admin  # can cause reload of the bootstrap file, among other things
  - subject: gx-scs
    api_key: "secret api key 2"
    public_key: "..."
```

## Endpoints

### POST /reports

Needs to be authenticated (via basic auth).

Needs to specify `Content-Type`, either `application/json` or `application/yaml`.

### GET /reports

Returns the most recent reports, by default restricted to the authenticated subject and limited to 10 items.

Needs to be authenticated (via basic auth).

Supports query parameters:

- `subject=SUBJECT`: by default, results are restricted to the subject of the authenticated account;
  if the account has the role `read_any`, any subject may be specified, or it may be left blank to remove
  the restriction;
- `limit=N`: return at most N items (default: 10);
- `skip=N`: skip N items (useful for pagination).

### GET /status/{subject}

Returns the current status of the subject. Use the `Accept` header to select desired content type:

- `text/html` (default): a snippet of HTML suitable for the end user;
- `image/png`: a PNG image of a badge;
- `application/json`: a short summary in JSON format.

NOTE: The result may differ depending on the authentication status. If the most recent report does not
indicate a conclusive pass, then an authenticated user will immediately see this. The public, on the other
hand, may only see this after some time window that allows manual verification of the result.

### GET /metrics/{subject}

A Prometheus exporter for the status of the subject.

Needs to be authenticated (via basic auth).

Supports content type `text/plain; version=0.0.4; charset=utf-8` only.

### GET /page/{subject}

Returns the certificate status page (HTML) for the subject.