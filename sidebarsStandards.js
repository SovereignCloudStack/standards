// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  standards: [
    "index",
    {
      type: "category",
      label: "Active",
      link: {
        type: "generated-index",
      },
      items: [
        "active/scs-0001-v1-sovereign-cloud-standards",
        "active/scs-0002-v1-standards-docs-org",
        "active/scs-0003-v1-sovereign-cloud-standards-yaml",
        "active/scs-0100-v3-flavor-naming",
        "active/scs-0101-v1-entropy",
        "active/scs-0102-v1-image-metadata",
        "active/scs-0110-v1-ssd-flavors",
        "active/scs-0210-v1-k8s-new-version-policy",
        "active/scs-0211-v1-kaas-default-storage-class",
        "active/scs-0300-v1-requirements-for-sso-identity-federation",
        "active/scs-0400-v1-status-page-create-decision",
      ],
    },
  ],
};

module.exports = sidebars;
