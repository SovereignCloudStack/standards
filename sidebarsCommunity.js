// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  community: [
    "index",
    "calendar",
    "collaboration",
    {
      type: "category",
      label: "Communication",
      items: ["communication/matrix"],
    },
    {
      type: "category",
      label: "Cloud Resources",
      items: [
        "cloud-resources/cloud-resources",
        "cloud-resources/getting-started-openstack",
        "cloud-resources/plusserver-gx-scs",
        "cloud-resources/wavestack",
      ],
    },
    {
      type: "category",
      label: "GitHub",
      items: [
        "github/branchprotection",
        "github/dco-and-licenses",
        "github/tips-and-tricks",
      ],
    },
    {
      type: "category",
      label: "Contribute",
      link: {
        type: "generated-index",
      },
      items: [
        "contribute/adding-docs-guide",
        "contribute/doc-files-structure-guide",
        "contribute/docs-workflow-explanation",
        "contribute/linting-guide",
        "contribute/local-docusaurus-development-guide",
        "contribute/styleguide",
      ],
    },
    "license-considerations",
  ],
};

module.exports = sidebars;
