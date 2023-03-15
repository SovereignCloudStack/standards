// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  community: [
    'index',
    'calendar',
    'community/collaboration',
    {
      type: 'category',
      label: 'Communication',
      items: [
        'community/communication/matrix'
      ]
    },
    {
      type: 'category',
      label: 'Cloud Resources',
      items: [
        'community/cloud-resources/cloud-resources',
        'community/cloud-resources/getting-started-openstack',
        'community/cloud-resources/plusserver-gx-scs',
        'community/cloud-resources/wavestack'
      ]
    },
    {
      type: 'category',
      label: 'GitHub',
      items: [
        'community/github/branchprotection',
        'community/github/dco-and-licenses',
        'community/github/tips-and-tricks'
      ]
    },
    {
      type: 'category',
      label: 'Contribute',
      items: [
        'community/contribute/adding-docs-guide',
        'community/contribute/doc-files-structure-guide',
        'community/contribute/docs-workflow-explanation'
        'community/contribute/linting-guide'
        'community/contribute/local-docusaurus-development-guide'
        'community/contribute/styleguide'
      ]
    },
    'community/license-considerations'
  ]
}

module.exports = sidebars
