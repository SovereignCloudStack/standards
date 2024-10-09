---
title: Cluster-API images
type: Decision Record
status: Draft
track: Iaas
---

## Abstract

The SCS reference implementation for the Kubernetes-as-a-service layer is built on top of Cluster API (CAPI), and therefore it depends on the corresponding VM images, which may or may not be present on the underlying infrastructure-as-a-service layer. Current tooling will make sure to upload the required image in case it's not present or outdated. However, these ad-hoc uploads will not be shared across environments, which may lead to waste of bandwidth (for transferring the image), storage (if images are not stored in a deduplicated manner), and not least time (because the upload does take multiple minutes). Needless to say, it may also lead to excessive greenhouse-gas emissions.

This decision record investigates the pros and cons of making the CAPI images mandatory. Ultimately, the decision is made to keep them recommended; we stress, however, that providers who offer the images by default should advertise this fact.

## Terminology

- _Kubernetes as a service (KaaS)_: A service that offers provisioning Kubernetes clusters.
- _Cluster API (CAPI)_: "Cluster API is a Kubernetes sub-project focused on providing declarative APIs and tooling to simplify provisioning, upgrading, and operating multiple Kubernetes clusters." ([source](https://cluster-api.sigs.k8s.io/)) This API can thus be used to implement KaaS.
- _CAPI image_: Virtual machine image that contains a standardized Kubernetes setup to be used for CAPI. The SCS reference implementation for KaaS depends on these images.
- _CSP_: Cloud-service provider

## Design considerations

We consider the following two options:

1. Make CAPI image mandatory.
2. Keep CAPI image recommended.

For reasons of symmetry, it suffices to consider the pros and cons of the first option.

Pros:

- Save time, money, physical resources and power for both CSP and customer.
- Regardless of CSP taste, this KaaS tech is part of SCS.

Neutral:

- The CAPI image can be provided in an automated fashion that means virtually no burden to the CSP.
- The KaaS implementation will work either way.
- Willing CSPs may offer the image by default and advertise as much.

Cons:

- Additional regulations would be necessary to guarantee quality and timeliness of image.
- Some CSPs may be opposed to being forced to offer a certain service, which may hurt the overall acceptance
  of the SCS standardization efforts.

## Decision

Ultimately, we value the freedom of the CSPs (and the acceptance of the standardization efforts) highest;
willing CSPs are welcome to opt in, i.e., to provide up-to-date images and advertise as much.

## Consequences

None, as the status quo is being kept.

## Open questions

Some interesting potential future work does remain, however: to find a way to certify that a willing provider
does indeed provide up-to-date images. It would be possible with today's methods to certify that a CAPI
image is present (the image_spec yaml file would have to be split up to obtain a separate test case), but
we there is no way to make sure that the image is up to date.
