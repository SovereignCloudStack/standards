# Notes about the test data for unit tests

This README documents how the sample data in this directory was created. It is
supposed to be static (no need to update it) and used as part of the unit tests.

## releases.json

This file is used for testing parts of the conformance check algorithm without
actually connecting to the GitHub API.

It was created from real release data filtered for the interesting bits through
`jq` and intentionally contains fewer entries sufficient for testing:

```shell
RELEASE_PAGE='https://api.github.com/repos/kubernetes/kubernetes/releases?per_page=20'
curl -sS "$RELEASE_PAGE" | jq '[.[] | {name, tag_name, draft, prerelease, published_at}]'
```
