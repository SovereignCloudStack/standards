---
title: Cluster-API images
type: Decision Record
status: Draft
track: Iaas
---

<!---
This is a template striving to provide a starting point for
creating a decision record adhering to scs-0001.
Replace at least all text in the sections not marked as OPTIONAL.
See https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0001-v1-sovereign-cloud-standards.md
--->

## Abstract

The problem that brings us here is how to update and keep track with upstream kubernetes versions when using the cluster-stacks approach on OpenStack. As the [SCS K8S Version Policy](https://docs.scs.community/standards/scs-0210-v2-k8s-version-policy#motivation) formulates, SCS is quite eager to keep track with the upstream work and does not want to fall behind:

> We want to achieve an up-to-date policy, meaning that providers should be mostly in sync with the upstream and don't fall behind the official Kubernetes releases.

## Context

The following scenario: 1 CSP with 100 customers each deploying at least one cluster.
One image will be downloaded (from upstream) and uploaded (to glance) and stored 99 times.

## Decision

Mandate the CSP to keep cluster-api Images up-to-date.

From the meeting notes:

- will save time and money for both CSP and customer
- would guarantee quality and timelness of image
- regardless of CSP taste, this KaaS tech is part of SCS
- CSP won't have noticable disadvantages from providing the image

This would lead to the following standard changes:
Create a copy of the [default image list](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml) and change the capi block from "recommended" to "mandatory".

Also, strictly speaking, we have to change [the standard image format definition](https://github.com/SovereignCloudStack/standards/blob/main/Standards/scs-0104-v1-standard-images.md#image-specification-class-of-images) so that "mandatory" for an image class does not mean that at least one image MUST be present in glance but all that match the [SCS K8S Version Policy](https://docs.scs.community/standards/scs-0210-v2-k8s-version-policy#motivation). Also the checking script has to be adapted.

## Consequences

CSPs will have the additional burden to provide cluster-api images in glance (and update them regularly).

The CSP will save bandwitdth and diskspace when images are only downloaded and stored once, instead of per Customer.
It will be easier and quicker for customers to update their clusters.
