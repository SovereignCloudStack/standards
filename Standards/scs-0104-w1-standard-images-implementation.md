---
title: "SCS Standard Images: Implementation and Testing Notes"
type: Supplement
track: IaaS
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

### Option A: pragmatic

Run the test script on your environment and check the error messages :)

1. Check out the [standards repository](https://github.com/SovereignCloudStack/standards).

   ```shell
   git clone https://github.com/SovereignCloudStack/standards.git
   cd standards
   ```

2. Install requirements:

   ```shell
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt 
   ```

3. Make sure that your `OS_CLOUD` environment variable is set.
4. Run the main check script:

   ```shell
   python3 ./Tests/scs-compliance-check.py ./Tests/scs-compatible-iaas.yaml -t standard-images-check \
     -s $OS_CLOUD -a os_cloud=$OS_CLOUD -o report.yaml -C
   ```

5. Inspect console output (stderr) for error messages.

### Option B: principled

1. Find your intended version of the certificate scope in the [overview table](https://docs.scs.community/standards/scs-compatible-iaas). It will most likely be one whose 'State' is 'Effective' or 'Stable'.
2. In (or below) the row labeled 'scs-0104: Standard images', you find a link to the YAML file that lists mandatory and recommended images, such as [scs-0104-v1-images.yaml](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/scs-0104-v1-images.yaml) for v4 of the certificate scope.
3. For each entry under `images`, ensure the following (either manually or by using the OpenStack Image Manager described in the section "Operational Tooling"):
   - if the entry says `status: mandatory`, your environment MUST provide this image, i.e., an image whose name matches the `name_scheme` or (in absence of a name scheme) the `name`.
   - every actual image in your environment _that matches the `name_scheme` or (in absence of a name scheme) the `name`_ has the correct `image_source` property: its value MUST start with one of the prefixes listed under `source`.

## Operational Tooling

The [openstack-image-manager](https://github.com/osism/openstack-image-manager) is able to
create all standard, mandatory SCS images for you given image definitions from a YAML file.
Please see [its documentation](https://docs.scs.community/docs/iaas/components/image-manager/) for details.

## Automated tests

We implemented testcases reflecting the information given in the YAML file(s). Be advised that
the approach with the YAML file has considerable drawbacks, and it will be abandoned in
future versions of the standard in favor of a more classical approach. The testcases already
anticipate this future development.

There are two classes of testcases:

- `scs-0104-source-X` with varying `X`:
  these ensure that certain images have the correct `image_source`;
- `scs-0104-image-X` with varying `X`:
  these ensure that certain images can be found in the list of public images.

The testcases can be run using the script
[`openstack_test.py`](https://github.com/SovereignCloudStack/standards/blob/main/Tests/iaas/openstack_test.py).
