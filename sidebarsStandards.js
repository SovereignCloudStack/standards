// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  standards: [
    'index',
    {
      type: 'category',
      label: 'Active',
      link: {
        type: 'generated-index'
      },
      items: [
        'scs-0001-v1-sovereign-cloud-standards',
        'scs-0002-v1-standards-docs-org',
        'scs-0003-v1-sovereign-cloud-standards-yaml',
        'scs-0100-v2-flavor-naming',
        'scs-0101-v1-entropy',
        'scs-0110-v1-ssd-flavors',
        'scs-0210-v1-k8s-new-version-policy',
        'scs-0211-v1-kaas-default-storage-class',
        'scs-0300-v1-requirements-for-sso-identity-federation',
        'scs-0400-v1-status-page-create-decision',
      ]
    }
  ]
}

module.exports = sidebars
