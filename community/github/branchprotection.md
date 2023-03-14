# Branch Protection Rules

To protect our source code from unwanted changes, we enforce the following branch protection rules for all repositories within our [GitHub organization](https://github.com/SovereignCloudStack):

- Require a pull request before merging into our default branch `main`.
  - Require at least one approval before pull requests can be merged.
  - Dismiss stale pull request approvals when new commits are pushed
- Require status checks to pass before merging
  - Require branches to be up to date before merging
  - Status checks that are required:
    - [DCO](dco-and-licenses.md)
- Do not allow bypassing the above settings

The branch protection rules are rolled out by our [`github-manager`](https://github.com/SovereignCloudStack/github-manager) to ensure that all repositories use a consistent set of rules. Should you intend to propose changes to the above rules, please open a pull request against [`orgs/SovereignCloudStack/data.yaml`](https://github.com/SovereignCloudStack/github-manager/blob/main/orgs/SovereignCloudStack/data.yaml).

Some repositories however do allow that the above rules are bypassed by the organization's owners, especially repositories that are used for public resources such as the website or the weekly digest.
