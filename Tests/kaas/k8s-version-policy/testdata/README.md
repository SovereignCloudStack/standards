# Testdata for unit tests

## releases.json

was created from real release data filtered through `jq`:

```shell
RELEASE_PAGE='https://api.github.com/repos/kubernetes/kubernetes/releases?per_page=20'
curl -sS "$RELEASE_PAGE" | jq '[.[] | {name, tag_name, draft, prerelease, published_at}]'
```
