// @ts-check

/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  community: [
    'index',
    'calendar',
    {
      type: 'category',
      label: 'Contribute',
      items: [
        'contribute/collaboration',
        'contribute/license-considerations',
        'contribute/dco-and-licenses'
      ]
    }
  ]
}

module.exports = sidebars
