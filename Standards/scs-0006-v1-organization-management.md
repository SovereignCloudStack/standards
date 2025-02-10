---
title: SCS GitHub Organization - Management of Inactive Users and Repositories
type: Procedural
status: Draft
track: Global
description: |
  SCS-0006 defines how the SCS GitHub organization identifies and handles inactive users and stale repositories.
  It ensures that only active contributors remain in the organization and that outdated repositories are archived to
  keep the environment organized and relevant.
---

## Introduction

To keep the SCS GitHub organization active and well-maintained, we regularly review user activity and repository relevance.
Inactive users are removed to ensure security and engagement, while outdated repositories are archived to keep the
workspace clean and efficient. This document outlines the criteria for identifying inactivity and the steps taken to manage it.

## Definitions

### Inactive User

A member of the SCS GitHub organization who has not engaged in any of the following activities within the past **365** days:

- Creating or commenting on pull requests (PRs) or issues within SCS GitHub repositories.
- Pushing commits to any repository within the organization.
- Participating in code reviews or other interactions within the SCS GitHub organization.

### Stale Repository

A repository within the SCS GitHub organization that has not experienced any of the following activities for a continuous period of **183** days:

- Commits or code merges.
- Issue creation or comments.
- Pull request submissions or reviews.
- Updates to documentation or other repository content.

## Procedures

### Identification of Inactive Users

On a monthly basis, organization owners will review user activity logs to identify members who meet the inactivity criteria.
Identified inactive users will be notified via email, reminding them of their inactivity and encouraging re-engagement with the organization's projects.

### Management of Inactive Users

If a user remains inactive for an additional 30 days after the initial notification (totaling 395 days of inactivity),
the user will be designated as dormant. Dormant users will be removed from the SCS GitHub organization to maintain security
and active collaboration. They may request reactivation by contacting the organization owners and expressing their intent to contribute.

### Identification of Stale Repositories

On a monthly basis, organization owners will assess all repositories for activity levels.
Repositories identified as stale will be flagged for review.

### Management of Stale Repositories

Maintainers of repositories deemed stale will be contacted to determine the repository's relevance and future plans.
If maintainers confirm that the repository is no longer active or necessary, or if no response is received within 30 days,
(totaling 213 days of inactivity) the repository will be archived. Archiving a repository makes it read-only, preserving
its content for reference while indicating that it is no longer actively maintained.

## Conclusion

By systematically managing inactive users and stale repositories, the SCS GitHub organization ensures that its collaborative
environment remains secure, efficient, and focused on active projects. This proactive approach fosters a culture of engagement
and maintains the integrity and relevance of the organization's resources.
