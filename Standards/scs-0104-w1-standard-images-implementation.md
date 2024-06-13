---
title: "SCS Standard Images Standard: Implementation Notes"
type: Supplement
track: IaaS
status: Proposal
supplements:
  - scs-0104-v1-standard-images.md
---

## Introduction

The SCS standard on standard images does not in itself lay down what images are actually
required or recommended; rather it specifies the format of a YAML file that in turn serves
said purpose. The particular YAML file that an implementer (a cloud service provider or operator)
has to comply with is given in the respective version of the certificate scope "SCS-compatible IaaS"
as a parameter to the standard. This document is intended to give implementers a
step-by-step guide on how to comply with the SCS certificate scope.

## Step-by-step walkthrough

1. Find your intended version of the certificate scope in the [overview table](https://docs.scs.community/standards/scs-compatible-iaas). It will most likely be one whose 'State' is 'Effective' or 'Stable'.
2. In (or below) the row labeled 'scs-0104: Standard images', you find a link to the YAML file that lists mandatory and recommended images, such as  [scs-0104-v1-images.yaml](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml) for v4 of the certificate scope.
3. For each entry under `images`, ensure the following (either manually or by using the OpenStack Image Manager described in the section "Operational Tooling"):
   - if the entry says `status: mandatory`, your environment MUST provide this image, i.e., an image whose name matches the `name_scheme` or (in absence of a name scheme) the `name`.
   - every actual image in your environment _that matches the `name_scheme` or (in absence of a name scheme) the `name`_ has the correct `image_source` property: its value MUST start with one of the prefixes listed under `source`.

## Operational Tooling

The [openstack-image-manager](https://github.com/osism/openstack-image-manager) is able to
create all standard, mandatory SCS images for you given image definitions from a YAML file.
Please see [its documentation](https://docs.scs.community/docs/iaas/components/image-manager/) for details.
